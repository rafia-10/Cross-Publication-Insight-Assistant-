import os
import json
from typing import List, Tuple

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
    except Exception:
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

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for fname in files:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, repo_path)
            _, ext = os.path.splitext(fname.lower())

            try:
                if os.path.getsize(fpath) > MAX_FILE_SIZE:
                    continue
            except OSError:
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
            except Exception:
                continue
        if text.strip():
            results.append((rel, text))

    return results
