import time
import json
from typing import Optional
from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.router import route_query, decide_route
from app.agents.fact_checker import FactCheckerAgent
from app.agents.summarizer import SummarizerAgent
from app.tools.aggregate_calculations import aggregate_technologies, get_most_common_technologies
from app.agents.query_agent import QueryAgent
from app.core.logging import get_logger
from app.core.exceptions import InsightAssistantError

logger = get_logger(__name__)


# --------------------------------------------------------------------------
# Helper: wrap a node function with entry/exit logging and error capture
# --------------------------------------------------------------------------

def _timed_node(name: str, fn):
    """
    Decorator that logs entry/exit of a graph node and captures
    InsightAssistantError into state["error"] for graceful degradation.
    """
    def wrapper(state: GraphState) -> GraphState:
        logger.debug("Node entered", extra={"node": name})
        t0 = time.perf_counter()
        try:
            result = fn(state)
            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.info(
                "Node completed",
                extra={"node": name, "duration_ms": duration_ms},
            )
            return result
        except InsightAssistantError as e:
            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.error(
                "Node raised application error",
                extra={
                    "node": name,
                    "error_type": type(e).__name__,
                    "error": e.message,
                    "context": e.context,
                    "duration_ms": duration_ms,
                },
                exc_info=e.cause,
            )
            return {**state, "error": f"[{name}] {e.message}"}
        except Exception as e:
            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.exception(
                "Node raised unexpected error",
                extra={"node": name, "duration_ms": duration_ms},
            )
            return {**state, "error": f"[{name}] Unexpected error: {e}"}
    wrapper.__name__ = name
    return wrapper


# --------------------------------------------------------------------------
# Node implementations
# --------------------------------------------------------------------------

def _aggregate_node(state: GraphState) -> GraphState:
    """Runs deterministic aggregate math over project analyses."""
    projects = state.get("projects_analysis") or []
    attr = state.get("target_attribute") or "frameworks"
    val = state.get("target_value") or ""

    logger.debug(
        "Aggregate node",
        extra={"project_count": len(projects), "attribute": attr, "value": val},
    )

    if val:
        result = aggregate_technologies(projects, attr, val)
    else:
        result = get_most_common_technologies(projects, attr)

    return {**state, "aggregate_result": result}


def _rag_node(state: GraphState) -> GraphState:
    """Performs semantic vector search for relevant project content."""
    from app.database.vector_store import search_project_knowledge

    terms = state.get("search_terms") or []
    project_ids = state.get("project_ids")
    query = " ".join(terms) if terms else state["user_query"]

    logger.debug(
        "RAG node",
        extra={"query_preview": query[:80], "project_ids": project_ids},
    )

    chunks = search_project_knowledge(query, project_ids=project_ids)
    logger.info("RAG retrieval complete", extra={"chunks_retrieved": len(chunks)})
    return {**state, "retrieved_chunks": chunks, "rag_result": chunks}


def _compare_node(state: GraphState) -> GraphState:
    """Groups project analyses by their primary framework and compares them."""
    projects = state.get("projects_analysis") or []
    terms = state.get("search_terms") or []

    logger.debug("Compare node", extra={"project_count": len(projects)})

    groups: dict = {}
    for proj in projects:
        frameworks = proj.get("agent_frameworks") or proj.get("frameworks") or []
        key = frameworks[0]["technology"] if frameworks else "Other"
        groups.setdefault(key, []).append(proj.get("project_name"))

    compare_result = {
        "groups": groups,
        "total_projects": len(projects),
        "search_terms": terms,
    }
    logger.info("Compare node complete", extra={"group_count": len(groups)})
    return {**state, "compare_result": compare_result}


def _fact_checker_node(state: GraphState) -> GraphState:
    """Verifies the result against retrieved evidence."""
    # Short-circuit if a previous node already captured an error
    if state.get("error"):
        logger.warning(
            "Skipping fact-check due to upstream error",
            extra={"upstream_error": state["error"]},
        )
        result = {"status": "unverified", "reasoning": "Skipped due to upstream error.", "supporting_evidence": []}
        return {**state, "fact_check_result": result}

    checker = FactCheckerAgent()

    # Build the claim to verify from whichever path produced a result
    if state.get("aggregate_result"):
        r = state["aggregate_result"]
        claim = (
            f"{r.get('matching', 0)} of {r.get('total', 0)} projects "
            f"({r.get('percentage', 0)}%) use {r.get('target_value', 'the technology')}."
        )
        evidence = [p.get("source_url", "") for p in r.get("matching_projects", [])]
    elif state.get("rag_result"):
        chunks = state["rag_result"]
        claim = f"Projects related to: {state.get('user_query')}"
        evidence = [c.get("chunk", "") for c in chunks]
    elif state.get("compare_result"):
        r = state["compare_result"]
        claim = f"Comparison of project groups: {list(r.get('groups', {}).keys())}"
        evidence = [json.dumps(r.get("groups", {}))]
    else:
        result = {"status": "unverified", "reasoning": "No results to verify.", "supporting_evidence": []}
        return {**state, "fact_check_result": result}

    fact_result = checker.verify(claim, evidence)
    return {**state, "fact_check_result": fact_result.model_dump()}


def _summarizer_node(state: GraphState) -> GraphState:
    """Produces the final natural language answer."""
    # Surface error if pipeline is in a failed state
    if state.get("error") and not any([
        state.get("aggregate_result"), state.get("rag_result"), state.get("compare_result")
    ]):
        logger.warning("Summariser returning error message from graph state")
        return {**state, "final_answer": f"The query could not be completed: {state['error']}"}

    summarizer = SummarizerAgent()

    structured_results = (
        state.get("aggregate_result") or
        state.get("rag_result") or
        state.get("compare_result") or {}
    )
    fact_check = state.get("fact_check_result") or {}

    answer = summarizer.summarize(state["user_query"], structured_results, fact_check)
    return {**state, "final_answer": answer}


def _unsupported_node(state: GraphState) -> GraphState:
    """Handles queries the system cannot answer."""
    logger.info("Query classified as unsupported", extra={"query_preview": state.get("user_query", "")[:80]})
    return {
        **state,
        "final_answer": (
            "I'm sorry, this system can only answer questions about technologies, "
            "frameworks, patterns, and trends across analyzed GitHub repositories and publications."
        ),
    }


# Wrap all nodes with timing and error capture
aggregate_node = _timed_node("aggregate_node", _aggregate_node)
rag_node = _timed_node("rag_node", _rag_node)
compare_node = _timed_node("compare_node", _compare_node)
fact_checker_node = _timed_node("fact_checker_node", _fact_checker_node)
summarizer_node = _timed_node("summarizer_node", _summarizer_node)
unsupported_node = _timed_node("unsupported_node", _unsupported_node)


# --------------------------------------------------------------------------
# Graph assembly
# --------------------------------------------------------------------------

def build_query_graph():
    builder = StateGraph(GraphState)

    builder.add_node("router", route_query)
    builder.add_node("aggregate_node", aggregate_node)
    builder.add_node("rag_node", rag_node)
    builder.add_node("compare_node", compare_node)
    builder.add_node("fact_checker_node", fact_checker_node)
    builder.add_node("summarizer_node", summarizer_node)
    builder.add_node("unsupported_node", unsupported_node)

    builder.set_entry_point("router")

    builder.add_conditional_edges(
        "router",
        decide_route,
        {
            "aggregate_node": "aggregate_node",
            "rag_node": "rag_node",
            "compare_node": "compare_node",
            "unsupported_node": "unsupported_node",
        },
    )

    builder.add_edge("aggregate_node", "fact_checker_node")
    builder.add_edge("rag_node", "fact_checker_node")
    builder.add_edge("compare_node", "fact_checker_node")
    builder.add_edge("fact_checker_node", "summarizer_node")
    builder.add_edge("summarizer_node", END)
    builder.add_edge("unsupported_node", END)

    return builder.compile()


# Build the ingestion graph (simpler linear pipeline)
def build_ingestion_graph():
    from app.ingestion.indexer import index_project
    from langgraph.graph import StateGraph, END
    from typing import TypedDict

    class IngestionState(TypedDict):
        url: str
        source_type: str
        project_id: Optional[int]
        error: Optional[str]

    def fetch_and_index(state):
        try:
            result = index_project(state["url"], state.get("source_type", "github"))
            return {**state, "project_id": result}
        except InsightAssistantError as e:
            logger.error(
                "Ingestion graph error",
                extra={"url": state.get("url"), "error": e.message},
                exc_info=e.cause,
            )
            return {**state, "error": e.message}
        except Exception as e:
            logger.exception("Unexpected ingestion graph error", extra={"url": state.get("url")})
            return {**state, "error": str(e)}

    builder = StateGraph(IngestionState)
    builder.add_node("fetch_and_index", fetch_and_index)
    builder.set_entry_point("fetch_and_index")
    builder.add_edge("fetch_and_index", END)
    return builder.compile()


# Singleton compiled graph
query_graph = build_query_graph()
