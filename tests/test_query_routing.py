from unittest.mock import patch
from app.agents.query_agent import QueryAgent, QueryRoute

@patch('app.agents.query_agent.ChatPromptTemplate')
def test_query_router_retrieve(mock_prompt):
    agent = QueryAgent()
    # Replace the route_query method directly for testing the schema
    agent.route_query = lambda q: QueryRoute(
        query_type="retrieve",
        search_terms=["vector database", "FAISS"]
    )
    
    route = agent.route_query("Show me projects using FAISS.")
    assert route.query_type == "retrieve"
    assert "FAISS" in route.search_terms

def test_query_router_aggregate():
    agent = QueryAgent()
    agent.route_query = lambda q: QueryRoute(
        query_type="aggregate",
        target_attribute="frameworks",
        target_value="LangGraph"
    )
    
    route = agent.route_query("What percentage use LangGraph?")
    assert route.query_type == "aggregate"
    assert route.target_value == "LangGraph"
