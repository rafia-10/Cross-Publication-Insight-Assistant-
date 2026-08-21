from app.graph.state import GraphState
from app.agents.query_agent import QueryAgent

_query_agent = QueryAgent()

def route_query(state: GraphState) -> GraphState:
    """
    Node: Classifies the user query and sets routing fields.
    """
    route = _query_agent.route_query(state["user_query"])
    return {
        **state,
        "query_type": route.query_type,
        "target_attribute": route.target_attribute,
        "target_value": route.target_value,
        "search_terms": route.search_terms,
    }

def decide_route(state: GraphState) -> str:
    """
    Conditional edge function: returns the name of the next node based on query_type.
    """
    qt = state.get("query_type", "unsupported")
    if qt == "aggregate":
        return "aggregate_node"
    elif qt == "retrieve":
        return "rag_node"
    elif qt == "compare":
        return "compare_node"
    else:
        return "unsupported_node"
