import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from app.config import settings

class VectorStore:
    def __init__(self, collection_name: str = "project_knowledge"):
        self.persist_directory = settings.chroma_persist_directory
        # Initialize chroma client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
        api_key = settings.openrouter_api_key or os.environ.get("OPENROUTER_API_KEY") or settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        if api_key:
            is_openrouter = bool(settings.openrouter_api_key or os.environ.get("OPENROUTER_API_KEY"))
            base_url = settings.openrouter_base_url if is_openrouter else None
            self.embeddings = OpenAIEmbeddings(
                model=settings.openrouter_embedding_model or "text-embedding-3-small",
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.embeddings = None # Useful for mocking tests without API keys

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """
        Add documents to the vector store.
        """
        if not self.embeddings:
            return
            
        embeddings = self.embeddings.embed_documents(texts)
        self.collection.upsert(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, project_ids: Optional[List[int]] = None, n_results: int = 5) -> Dict[str, Any]:
        """
        Search for documents in the vector store.
        """
        if not self.embeddings:
            return {"documents": [], "metadatas": [], "distances": []}
            
        query_embedding = self.embeddings.embed_query(query)
        
        where = None
        if project_ids:
            if len(project_ids) == 1:
                where = {"project_id": project_ids[0]}
            else:
                where = {"project_id": {"$in": project_ids}}
                
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        return results

# Expose search tool
def search_project_knowledge(query: str, project_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    store = VectorStore()
    results = store.search(query, project_ids)
    
    formatted_results = []
    if results and "documents" in results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            score = results["distances"][0][i] if results.get("distances") else 0
            
            formatted_results.append({
                "chunk": doc,
                "metadata": meta,
                "similarity_score": score
            })
            
    return formatted_results
