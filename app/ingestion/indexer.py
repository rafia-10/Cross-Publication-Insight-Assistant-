import os
import uuid
import tempfile
import shutil
import stat
from typing import Optional
from sqlalchemy.orm import Session
from app.tools.github import fetch_github_repo, is_valid_github_url
from app.ingestion.parser import parse_repo
from app.ingestion.chunker import chunk_documents
from app.database.postgres import SessionLocal, init_db, get_project_by_url
from app.database.models import Project, VectorRecord
from app.database.vector_store import VectorStore

def _remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def index_project(url: str, source_type: str = "github") -> Optional[int]:
    """
    Full ingestion pipeline:
    1. Fetch the repo
    2. Parse files
    3. Chunk documents
    4. Store chunks in vector DB
    5. Record project in SQL DB
    Returns the project_id.
    """
    init_db()
    db: Session = SessionLocal()
    
    try:
        # Check if already indexed
        existing = get_project_by_url(db, url)
        if existing:
            return existing.id

        dest_dir = tempfile.mkdtemp(prefix="ingest_")
        
        try:
            if source_type == "github" and is_valid_github_url(url):
                fetch_result = fetch_github_repo(url, dest_dir=dest_dir)
                if fetch_result.error:
                    raise ValueError(f"Fetch error: {fetch_result.error}")
                repo_path = fetch_result.local_path
                project_name = fetch_result.metadata.get("repo_name", url.split("/")[-1])
            else:
                raise ValueError(f"Unsupported source_type: {source_type}")

            # Create DB record first to get the project_id
            project = Project(
                name=project_name,
                source_url=url,
                source_type=source_type,
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            project_id = project.id

            # Parse and chunk
            documents = parse_repo(repo_path)
            chunks = chunk_documents(documents, project_id)

            # Store in vector DB (only if API key is available)
            if chunks:
                try:
                    store = VectorStore()
                    texts = [c["text"] for c in chunks]
                    ids = [str(uuid.uuid4()) for _ in chunks]
                    metadatas = [
                        {
                            "project_id": c["project_id"],
                            "file_path": c["file_path"],
                            "chunk_index": c["chunk_index"],
                            "source_url": url,
                        }
                        for c in chunks
                    ]
                    store.add_documents(texts, metadatas, ids)
                    
                    # Record vector entries in SQL
                    for i, chunk in enumerate(chunks):
                        vr = VectorRecord(
                            project_id=project_id,
                            chunk_text=chunk["text"],
                            file_path=chunk["file_path"],
                            chroma_id=ids[i],
                        )
                        db.add(vr)
                    db.commit()
                except Exception as e:
                    # Non-fatal: index without vectors if embedding fails
                    print(f"[indexer] Warning: Vector embedding skipped: {e}")

            return project_id

        finally:
            shutil.rmtree(dest_dir, onerror=_remove_readonly)
    finally:
        db.close()
