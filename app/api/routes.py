from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.postgres import SessionLocal, init_db
from app.database.models import Project
from app.ingestion.indexer import index_project
from app.graph.workflow import query_graph

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
    for url in req.urls:
        try:
            pid = index_project(url, source_type=req.source_type)
            indexed.append({"url": url, "project_id": pid})
        except Exception as e:
            errors.append({"url": url, "error": str(e)})
    return AnalyzeResponse(indexed=indexed, errors=errors)

@router.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest, db: Session = Depends(get_db)):
    # Load projects_analysis from DB for aggregate/compare paths
    if req.project_ids:
        projects_db = db.query(Project).filter(Project.id.in_(req.project_ids)).all()
    else:
        projects_db = db.query(Project).all()

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QueryResponse(
        answer=final_state.get("final_answer") or "No answer generated.",
        query_type=final_state.get("query_type"),
        fact_check_status=final_state.get("fact_check_result", {}).get("status") if final_state.get("fact_check_result") else None,
    )

@router.get("/projects", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
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
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(
        id=p.id,
        name=p.name,
        source_url=p.source_url,
        source_type=p.source_type,
        analyzed_at=p.analyzed_at.isoformat() if p.analyzed_at else None,
    )
