from typing import List, Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)

CHUNK_SIZE = 512       # characters (not tokens, for simplicity without tiktoken)
CHUNK_OVERLAP = 100


def chunk_text(text: str, file_path: str, project_id: int) -> List[Dict[str, Any]]:
    """
    Splits a text into overlapping chunks, preserving source metadata.
    """
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_content = text[start:end]

        if chunk_content.strip():
            chunks.append({
                "text": chunk_content,
                "file_path": file_path,
                "project_id": project_id,
                "chunk_index": chunk_index,
                "char_start": start,
                "char_end": end,
            })
            chunk_index += 1

        start += CHUNK_SIZE - CHUNK_OVERLAP  # move forward with overlap

    logger.debug(
        "File chunked",
        extra={"file_path": file_path, "chunk_count": len(chunks)},
    )
    return chunks


def chunk_documents(documents: List[tuple], project_id: int) -> List[Dict[str, Any]]:
    """
    Chunk a list of (file_path, text) tuples for a given project.
    """
    all_chunks = []
    for file_path, text in documents:
        all_chunks.extend(chunk_text(text, file_path, project_id))
    logger.debug(
        "All documents chunked",
        extra={"document_count": len(documents), "total_chunks": len(all_chunks)},
    )
    return all_chunks
