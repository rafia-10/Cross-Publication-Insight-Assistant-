import os
import tempfile
import pytest
from sqlalchemy.orm import Session
from app.database.postgres import engine, init_db, get_project_by_url, get_technology_by_name
from app.database.models import Project, Technology
from app.database.vector_store import VectorStore
from app.config import settings

def test_database_initialization():
    from sqlalchemy import create_engine
    with tempfile.TemporaryDirectory() as tmpdirname:
        db_path = os.path.join(tmpdirname, "test.db")
        test_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
        
        # Create a test engine directly
        test_engine = create_engine(test_url)
        try:
            # Initialize
            from app.database.models import Base
            Base.metadata.create_all(bind=test_engine)
            assert os.path.exists(db_path)
        finally:
            test_engine.dispose()

def test_vector_store_initialization():
    # Provide ignore_errors to TemporaryDirectory if python 3.10+, or just handle it
    tmpdirname = tempfile.mkdtemp()
    try:
        settings.chroma_persist_directory = tmpdirname
        # Should initialize without errors
        store = VectorStore(collection_name="test_collection")
        assert store.collection.name == "test_collection"
        # Close chroma if possible, but python API for Chroma 0.4+ might not have a clean close
    finally:
        import shutil
        shutil.rmtree(tmpdirname, ignore_errors=True)
