from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.postgres import SessionLocal, init_db
from app.database.models import Project
from app.ingestion.indexer import index_project
from app.graph.workflow import query_graph
from app.core.logging import get_logger
from app.core.exceptions import InsightAssistantError

logger = get_logger(__name__)
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---- Request/Response Models ----
class AnalyzeRequest(BaseModel):
    urls: List[str]
    source_type: str = "github"

class AnalyzeResponse(BaseModel):
    indexed: List[dict]
    errors: List[dict]

class QueryRequest(BaseModel):
    user_query: str
    project_ids: Optional[List[int]] = None

class QueryResponse(BaseModel):
    answer: str
    query_type: Optional[str] = None
    fact_check_status: Optional[str] = None

class ProjectOut(BaseModel):
    id: int
    name: str
    source_url: str
    source_type: str
    analyzed_at: Optional[str] = None


# ---- Routes ----

@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/projects/analyze", response_model=AnalyzeResponse)
def analyze_projects(req: AnalyzeRequest):
    init_db()
    indexed = []
    errors = []

    logger.info(
        "Analyze request received",
        extra={"url_count": len(req.urls), "source_type": req.source_type},
    )

    for url in req.urls:
        try:
            pid = index_project(url, source_type=req.source_type)
            indexed.append({"url": url, "project_id": pid})
            logger.info("Project indexed", extra={"url": url, "project_id": pid})
        except InsightAssistantError as e:
            logger.error(
                "Failed to index project",
                extra={
                    "url": url,
                    "error_type": type(e).__name__,
                    "error": e.message,
                    "context": e.context,
                },
                exc_info=e.cause,
            )
            errors.append({"url": url, "error": e.message})
        except Exception as e:
            logger.exception("Unexpected error indexing project", extra={"url": url})
            errors.append({"url": url, "error": str(e)})

    logger.info(
        "Analyze request complete",
        extra={"indexed": len(indexed), "errors": len(errors)},
    )
    return AnalyzeResponse(indexed=indexed, errors=errors)


@router.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest, db: Session = Depends(get_db)):
    logger.info(
        "Query request received",
        extra={
            "user_query": req.user_query[:120],
            "project_ids": req.project_ids,
        },
    )

    # Load projects from DB
    if req.project_ids:
        projects_db = db.query(Project).filter(Project.id.in_(req.project_ids)).all()
    else:
        projects_db = db.query(Project).all()

    logger.debug("Projects loaded for query", extra={"project_count": len(projects_db)})

    # Represent each project as a minimal dict (full analysis would need joined tables)
    projects_analysis = [
        {
            "project_name": p.name,
            "source_url": p.source_url,
            "source_type": p.source_type,
            "frameworks": [],
            "agent_frameworks": [],
        }
        for p in projects_db
    ]

    initial_state = {
        "user_query": req.user_query,
        "project_ids": req.project_ids,
        "projects_analysis": projects_analysis,
        "query_type": None,
        "target_attribute": None,
        "target_value": None,
        "search_terms": None,
        "retrieved_chunks": None,
        "aggregate_result": None,
        "rag_result": None,
        "compare_result": None,
        "fact_check_result": None,
        "final_answer": None,
        "error": None,
    }

    try:
        final_state = query_graph.invoke(initial_state)
    except InsightAssistantError as e:
        logger.error(
            "Agent pipeline error",
            extra={"error_type": type(e).__name__, "error": e.message},
            exc_info=e.cause,
        )
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        logger.exception("Unexpected error in query pipeline")
        raise HTTPException(status_code=500, detail=str(e))

    # Surface any error the graph stored in state
    if final_state.get("error"):
        logger.warning(
            "Query completed with graph-level error",
            extra={"graph_error": final_state["error"]},
        )

    logger.info(
        "Query request complete",
        extra={"query_type": final_state.get("query_type")},
    )

    return QueryResponse(
        answer=final_state.get("final_answer") or "No answer generated.",
        query_type=final_state.get("query_type"),
        fact_check_status=(
            final_state.get("fact_check_result", {}).get("status")
            if final_state.get("fact_check_result")
            else None
        ),
    )


@router.get("/projects", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    logger.debug("Listing all projects")
    projects = db.query(Project).all()
    return [
        ProjectOut(
            id=p.id,
            name=p.name,
            source_url=p.source_url,
            source_type=p.source_type,
            analyzed_at=p.analyzed_at.isoformat() if p.analyzed_at else None,
        )
        for p in projects
    ]


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    logger.debug("Fetching project", extra={"project_id": project_id})
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        logger.warning("Project not found", extra={"project_id": project_id})
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(
        id=p.id,
        name=p.name,
        source_url=p.source_url,
        source_type=p.source_type,
        analyzed_at=p.analyzed_at.isoformat() if p.analyzed_at else None,
    )
