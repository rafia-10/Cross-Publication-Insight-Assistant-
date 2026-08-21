import os
from typing import List, Dict, Any
from pydantic import BaseModel

class SearchResult(BaseModel):
    file_path: str
    content_snippet: str
    line_number: int

# Priority files and extensions
PRIORITY_FILES = {"readme.md", "requirements.txt", "pyproject.toml", "setup.py", "package.json"}
PRIORITY_EXTENSIONS = {".py", ".ipynb", ".yaml", ".yml", ".json", ".md", ".txt", ".toml", ".rst"}
MAX_FILE_SIZE_BYTES = 1024 * 1024 # 1MB guard

def _get_files_to_search(repo_path: str) -> List[str]:
    files_to_search = []
    
    # Priority queues
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories like .git
        dirs[:] = [d for d in dirs if d != ".git"]
        
        for file in files:
            file_path = os.path.join(root, file)
            # Skip symlinks or unreadable files
            if not os.path.isfile(file_path):
                continue
                
            try:
                # Max file size guard
                if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
                    continue
            except OSError:
                continue

            lower_name = file.lower()
            _, ext = os.path.splitext(lower_name)
            
            if lower_name in PRIORITY_FILES:
                high_priority.append(file_path)
            elif ext in PRIORITY_EXTENSIONS:
                medium_priority.append(file_path)
            else:
                low_priority.append(file_path)
                
    # Sort files to search by priority
    return high_priority + medium_priority + low_priority

def search_repository(repo_path: str, query: str, max_results: int = 10, context_lines: int = 2) -> List[SearchResult]:
    """
    Searches files within a repository for a query string.
    Returns file path, content snippet, and line numbers.
    """
    if not os.path.exists(repo_path):
        return []

    query_lower = query.lower()
    results = []
    files_to_search = _get_files_to_search(repo_path)
    
    for file_path in files_to_search:
        if len(results) >= max_results:
            break
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            continue # Skip binary files or non-utf-8 text
        except Exception:
            continue
            
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                # Extract context
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                snippet = "".join(lines[start:end])
                
                # Use relative path from repo root
                rel_path = os.path.relpath(file_path, repo_path)
                
                results.append(SearchResult(
                    file_path=rel_path,
                    content_snippet=snippet,
                    line_number=i + 1
                ))
                
                if len(results) >= max_results:
                    break
                    
    return results
