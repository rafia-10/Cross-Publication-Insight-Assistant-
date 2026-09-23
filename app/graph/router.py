from app.graph.state import GraphState
from app.agents.query_agent import QueryAgent
from app.core.logging import get_logger
from app.core.exceptions import RoutingError

logger = get_logger(__name__)

_query_agent = QueryAgent()


def route_query(state: GraphState) -> GraphState:
    """
    Node: Classifies the user query and sets routing fields.
    Raises RoutingError if the LLM call fails.
    """
    query = state["user_query"]
    logger.info("Routing query", extra={"query_preview": query[:120]})

    try:
        route = _query_agent.route_query(query)
    except Exception as e:
        raise RoutingError(
            "Query routing LLM call failed",
            context={"query_preview": query[:120]},
            cause=e,
        ) from e

    logger.info(
        "Query classified",
        extra={
            "query_type": route.query_type,
            "target_attribute": route.target_attribute,
            "target_value": route.target_value,
            "search_terms": route.search_terms,
        },
    )

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
    logger.debug("Deciding route", extra={"query_type": qt})
    if qt == "aggregate":
        return "aggregate_node"
    elif qt == "retrieve":
        return "rag_node"
    elif qt == "compare":
        return "compare_node"
    else:
        return "unsupported_node"
