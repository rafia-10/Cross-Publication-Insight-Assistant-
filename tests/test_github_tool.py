import os
import shutil
import tempfile
import pytest
from app.tools.github import is_valid_github_url, fetch_github_repo

def test_is_valid_github_url():
    assert is_valid_github_url("https://github.com/langchain-ai/langgraph") is True
    assert is_valid_github_url("http://github.com/owner/repo") is True
    assert is_valid_github_url("https://github.com/owner/repo.git") is True
    assert is_valid_github_url("https://gitlab.com/owner/repo") is False
    assert is_valid_github_url("https://github.com/owner") is False
    assert is_valid_github_url("not_a_url") is False

def test_fetch_github_repo_invalid():
    result = fetch_github_repo("https://gitlab.com/owner/repo")
    assert result.error == "Invalid GitHub URL"
    assert result.local_path == ""

def test_fetch_github_repo_valid():
    # We will test with a small real repo to ensure clone works
    # Using a fast, small public repo like a demo or even a simple one
    test_url = "https://github.com/octocat/Hello-World"
    dest_dir = tempfile.mkdtemp()
    try:
        result = fetch_github_repo(test_url, dest_dir=dest_dir)
        assert result.error is None
        assert os.path.exists(result.local_path)
        assert os.path.isdir(os.path.join(result.local_path, ".git"))
        assert result.metadata["owner"] == "octocat"
        assert result.metadata["repo_name"] == "Hello-World"
        assert "commit_hash" in result.metadata
    finally:
        if os.path.exists(dest_dir):
            import stat
            def remove_readonly(func, path, _):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(dest_dir, onerror=remove_readonly)
