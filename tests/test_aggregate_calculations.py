import pytest
from app.tools.aggregate_calculations import calculate_percentage, aggregate_technologies, get_most_common_technologies

def test_calculate_percentage():
    res = calculate_percentage(3, 8)
    assert res["matching"] == 3
    assert res["total"] == 8
    assert res["percentage"] == 37.5
    
    res_zero = calculate_percentage(0, 0)
    assert res_zero["percentage"] == 0.0

def test_aggregate_technologies():
    mock_projects = [
        {"project_name": "A", "frameworks": [{"technology": "LangGraph"}], "source_url": "urlA"},
        {"project_name": "B", "frameworks": [{"technology": "LangChain"}], "source_url": "urlB"},
        {"project_name": "C", "frameworks": [{"technology": "langgraph"}], "source_url": "urlC"},
        {"project_name": "D", "frameworks": [], "source_url": "urlD"}
    ]
    
    result = aggregate_technologies(mock_projects, "frameworks", "LangGraph")
    assert result["matching"] == 2
    assert result["total"] == 4
    assert result["percentage"] == 50.0
    assert len(result["matching_projects"]) == 2
    assert result["matching_projects"][0]["project_name"] == "A"
    
def test_get_most_common_technologies():
    mock_projects = [
        {"project_name": "A", "databases": [{"technology": "PostgreSQL"}, {"technology": "Redis"}]},
        {"project_name": "B", "databases": [{"technology": "PostgreSQL"}]},
        {"project_name": "C", "databases": [{"technology": "MongoDB"}]}
    ]
    
    result = get_most_common_technologies(mock_projects, "databases", top_n=2)
    assert len(result) == 2
    assert result[0]["name"] == "PostgreSQL"
    assert result[0]["count"] == 2
    assert result[1]["name"] in ["Redis", "MongoDB"] # Ties for 2nd
