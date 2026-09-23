import os
import json
from typing import List, Tuple
from app.core.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".md", ".py", ".txt", ".toml", ".yaml", ".yml", ".json", ".rst"}
MAX_FILE_SIZE = 1024 * 1024  # 1MB
MAX_FILES_PER_REPO = 50


def extract_notebook_text(filepath: str) -> str:
    """Extract readable text from a Jupyter notebook."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            nb = json.load(f)
        texts = []
        for cell in nb.get("cells", []):
            source = cell.get("source", [])
            if isinstance(source, list):
                texts.append("".join(source))
            elif isinstance(source, str):
                texts.append(source)
        return "\n\n".join(texts)
    except Exception as e:
        logger.debug(
            "Failed to extract notebook text — skipping",
            extra={"filepath": filepath, "reason": str(e)},
        )
        return ""


def parse_repo(repo_path: str) -> List[Tuple[str, str]]:
    """
    Extracts (relative_file_path, text_content) from a repository.
    Returns up to MAX_FILES_PER_REPO files, prioritizing important ones.
    """
    priority_files = {"readme.md", "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"}
    results: List[Tuple[str, str]] = []
    high_priority = []
    low_priority = []
    skipped_large = 0
    skipped_unreadable = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for fname in files:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, repo_path)
            _, ext = os.path.splitext(fname.lower())

            try:
                size = os.path.getsize(fpath)
                if size > MAX_FILE_SIZE:
                    logger.debug(
                        "Skipping oversized file",
                        extra={"file": rel, "size_bytes": size, "limit_bytes": MAX_FILE_SIZE},
                    )
                    skipped_large += 1
                    continue
            except OSError as e:
                logger.debug(
                    "Cannot stat file — skipping",
                    extra={"file": rel, "reason": str(e)},
                )
                skipped_unreadable += 1
                continue

            if fname.lower() in priority_files:
                high_priority.append((rel, fpath, ext))
            elif ext in SUPPORTED_EXTENSIONS or ext == ".ipynb":
                low_priority.append((rel, fpath, ext))

    ordered = high_priority + low_priority
    for rel, fpath, ext in ordered[:MAX_FILES_PER_REPO]:
        if ext == ".ipynb":
            text = extract_notebook_text(fpath)
        else:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception as e:
                logger.debug(
                    "Cannot read file — skipping",
                    extra={"file": rel, "reason": str(e)},
                )
                skipped_unreadable += 1
                continue
        if text.strip():
            results.append((rel, text))

    logger.info(
        "Repository parsed",
        extra={
            "files_parsed": len(results),
            "skipped_large": skipped_large,
            "skipped_unreadable": skipped_unreadable,
            "total_candidates": len(ordered),
        },
    )
    return results
