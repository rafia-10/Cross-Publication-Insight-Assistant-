import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.database.vector_store import search_project_knowledge
from app.config import settings, get_chat_llm

class QueryRoute(BaseModel):
    query_type: str = Field(..., description="aggregate, retrieve, compare, or unsupported")
    target_attribute: Optional[str] = Field(None, description="The specific attribute to analyze (e.g. frameworks)")
    target_value: Optional[str] = Field(None, description="The specific value to look for (e.g. LangGraph)")
    search_terms: List[str] = Field(default_factory=list, description="Keywords optimized for vector search")

class QueryAgent:
    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm if llm is not None else get_chat_llm(temperature=0)
            
    def route_query(self, user_query: str) -> QueryRoute:
        """
        Classifies the query and extracts necessary search parameters.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent query router. Classify the user query into one of: 'aggregate' (counting/percentages), 'retrieve' (finding specific examples/RAG), 'compare' (comparing two things), or 'unsupported' (unrelated to software projects).\n\nAlso extract search terms optimized for a vector database."),
            ("user", "{query}")
        ])
        
        router = prompt | self.llm.with_structured_output(QueryRoute)
        return router.invoke({"query": user_query})

    def retrieve_evidence(self, search_terms: List[str], project_ids: Optional[List[int]] = None, k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes the RAG retrieval phase using the vector database.
        Combines multiple search terms into a single semantic search or searches them individually.
        """
        combined_query = " ".join(search_terms)
        if not combined_query:
            return []
            
        results = search_project_knowledge(combined_query, project_ids=project_ids)
        return results
