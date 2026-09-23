import os
import uuid
import tempfile
import shutil
import stat
import time
from typing import Optional
from sqlalchemy.orm import Session
from app.tools.github import fetch_github_repo, is_valid_github_url
from app.ingestion.parser import parse_repo
from app.ingestion.chunker import chunk_documents
from app.database.postgres import SessionLocal, init_db, get_project_by_url
from app.database.models import Project, VectorRecord
from app.database.vector_store import VectorStore
from app.core.logging import get_logger
from app.core.exceptions import FetchError, EmbeddingError

logger = get_logger(__name__)


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

    logger.info("Starting ingestion pipeline", extra={"url": url, "source_type": source_type})
    pipeline_start = time.perf_counter()

    try:
        # Check if already indexed
        existing = get_project_by_url(db, url)
        if existing:
            logger.info(
                "Project already indexed — skipping",
                extra={"url": url, "project_id": existing.id},
            )
            return existing.id

        dest_dir = tempfile.mkdtemp(prefix="ingest_")

        try:
            # --- Step 1: Fetch ---
            t0 = time.perf_counter()
            if source_type == "github" and is_valid_github_url(url):
                logger.debug("Cloning GitHub repository", extra={"url": url})
                fetch_result = fetch_github_repo(url, dest_dir=dest_dir)
                if fetch_result.error:
                    raise FetchError(
                        f"Failed to fetch repository: {fetch_result.error}",
                        context={"url": url, "source_type": source_type},
                    )
                repo_path = fetch_result.local_path
                project_name = fetch_result.metadata.get("repo_name", url.split("/")[-1])
                logger.info(
                    "Repository cloned",
                    extra={
                        "url": url,
                        "project_name": project_name,
                        "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                    },
                )
            else:
                raise FetchError(
                    f"Unsupported source_type: {source_type!r}",
                    context={"url": url, "source_type": source_type},
                )

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
            logger.debug("Project record created", extra={"project_id": project_id})

            # --- Step 2 & 3: Parse and chunk ---
            t0 = time.perf_counter()
            documents = parse_repo(repo_path)
            chunks = chunk_documents(documents, project_id)
            logger.info(
                "Repository parsed and chunked",
                extra={
                    "project_id": project_id,
                    "file_count": len(documents),
                    "chunk_count": len(chunks),
                    "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                },
            )

            # --- Step 4: Store in vector DB (only if API key available) ---
            if chunks:
                t0 = time.perf_counter()
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
                    logger.info(
                        "Chunks embedded and stored",
                        extra={
                            "project_id": project_id,
                            "chunk_count": len(chunks),
                            "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                        },
                    )
                except EmbeddingError:
                    raise
                except Exception as e:
                    # Non-fatal: index without vectors if embedding fails
                    logger.warning(
                        "Vector embedding skipped — project indexed without semantic search",
                        extra={"project_id": project_id, "reason": str(e)},
                        exc_info=True,
                    )

            total_ms = round((time.perf_counter() - pipeline_start) * 1000, 1)
            logger.info(
                "Ingestion pipeline complete",
                extra={"project_id": project_id, "total_duration_ms": total_ms},
            )
            return project_id

        finally:
            shutil.rmtree(dest_dir, onerror=_remove_readonly)
    finally:
        db.close()
