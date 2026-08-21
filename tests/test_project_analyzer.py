import os
import pytest
from unittest.mock import MagicMock
from app.agents.project_analyzer import ProjectAnalyzer
from app.schemas.project import ProjectAnalysis

def test_project_analyzer_schema_mock():
    """
    Test that the ProjectAnalyzer can be initialized and returns the correct schema structure.
    We use a mocked LLM response since we don't want to make real API calls in unit tests.
    """
    # Create a mock agent result
    mock_analysis = ProjectAnalysis(
        project_name="Test Project",
        source_url="https://github.com/test/test",
        source_type="github",
        description="A test project",
        uses_rag=True
    )
    
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {
        "structured_response": mock_analysis,
        "messages": []
    }
    
    analyzer = ProjectAnalyzer()
    
    # Patch the agent creation to return our mock
    import app.agents.project_analyzer
    original_create = app.agents.project_analyzer.create_react_agent
    app.agents.project_analyzer.create_react_agent = MagicMock(return_value=mock_agent)
    
    try:
        result = analyzer.analyze("/dummy/path", "Test Project", "https://github.com/test/test")
        
        assert isinstance(result, ProjectAnalysis)
        assert result.project_name == "Test Project"
        assert result.uses_rag is True
        
        # Verify the agent was called
        mock_agent.invoke.assert_called_once()
    finally:
        # Restore original
        app.agents.project_analyzer.create_react_agent = original_create
