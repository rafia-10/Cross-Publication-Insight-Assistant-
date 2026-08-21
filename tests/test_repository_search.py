import os
import tempfile
import shutil
from app.tools.repository_search import search_repository

def test_search_repository():
    # Setup a dummy repository
    temp_repo = tempfile.mkdtemp()
    
    try:
        # Create some files
        readme_path = os.path.join(temp_repo, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# Test Repo\nThis project uses LangGraph and FAISS.\nEnjoy!")
            
        py_path = os.path.join(temp_repo, "main.py")
        with open(py_path, "w", encoding="utf-8") as f:
            f.write("import os\nfrom langchain import LLM\n\ndef main():\n    print('hello')\n")
            
        # Search for LangGraph
        results = search_repository(temp_repo, "langgraph")
        assert len(results) == 1
        assert results[0].file_path == "README.md"
        assert "This project uses LangGraph and FAISS" in results[0].content_snippet
        
        # Search for langchain
        results_py = search_repository(temp_repo, "langchain")
        assert len(results_py) == 1
        assert results_py[0].file_path == "main.py"
        assert "from langchain import LLM" in results_py[0].content_snippet
        assert results_py[0].line_number == 2
        
    finally:
        shutil.rmtree(temp_repo)
