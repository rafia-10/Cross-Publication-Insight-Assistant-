import os
import shutil
import time
import tempfile
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import git
from pydantic import BaseModel
from app.core.logging import get_logger
from app.core.exceptions import FetchError

logger = get_logger(__name__)


class RepoFetchResult(BaseModel):
    local_path: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


def is_valid_github_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() == "github.com" and len(parsed.path.strip("/").split("/")) >= 2
    except Exception:
        return False


def fetch_github_repo(url: str, dest_dir: Optional[str] = None, max_retries: int = 3) -> RepoFetchResult:
    """
    Clones a GitHub repository to a local directory.
    Uses exponential backoff for retries if the clone fails.
    Raises FetchError if all attempts are exhausted.
    """
    if not is_valid_github_url(url):
        logger.warning("Invalid GitHub URL rejected", extra={"url": url})
        return RepoFetchResult(local_path="", metadata={}, error="Invalid GitHub URL")

    if dest_dir is None:
        dest_dir = tempfile.mkdtemp(prefix="repo_")

    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    owner, repo_name = path_parts[0], path_parts[1]

    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    metadata = {
        "owner": owner,
        "repo_name": repo_name,
        "source_url": url,
    }

    # Exponential backoff for cloning
    for attempt in range(1, max_retries + 1):
        try:
            if os.path.exists(dest_dir) and os.listdir(dest_dir):
                # Clear directory if it exists and is not empty from previous failed attempt
                shutil.rmtree(dest_dir)
                os.makedirs(dest_dir)

            logger.debug(
                "Cloning repository",
                extra={"url": url, "attempt": attempt, "max_retries": max_retries},
            )
            repo = git.Repo.clone_from(url, dest_dir, depth=1)  # shallow clone for speed
            metadata["default_branch"] = repo.active_branch.name
            metadata["commit_hash"] = repo.head.commit.hexsha
            repo.close()
            logger.info(
                "Repository cloned successfully",
                extra={
                    "url": url,
                    "repo_name": repo_name,
                    "commit": metadata["commit_hash"][:8],
                    "attempt": attempt,
                },
            )
            return RepoFetchResult(local_path=dest_dir, metadata=metadata)

        except git.exc.GitCommandError as e:
            wait = 2 ** (attempt - 1)
            if attempt == max_retries:
                logger.error(
                    "Git clone failed — all retries exhausted",
                    extra={"url": url, "attempts": attempt},
                    exc_info=True,
                )
                return RepoFetchResult(
                    local_path="", metadata=metadata,
                    error=f"Git clone failed after {max_retries} attempts: {str(e)}",
                )
            logger.warning(
                "Git clone attempt failed — retrying",
                extra={"url": url, "attempt": attempt, "retry_in_seconds": wait},
            )
            time.sleep(wait)

        except Exception as e:
            logger.exception(
                "Unexpected error during repository fetch",
                extra={"url": url, "attempt": attempt},
            )
            return RepoFetchResult(
                local_path="", metadata=metadata,
                error=f"Unexpected error: {str(e)}",
            )

    return RepoFetchResult(local_path="", metadata=metadata, error="Failed to clone repository")
