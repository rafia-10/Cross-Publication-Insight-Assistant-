from typing import List, Dict, Any
from pydantic import BaseModel

class RouterTestCase(BaseModel):
    query: str
    expected_type: str
    expected_attribute: str = ""
    expected_value: str = ""

class FactCheckTestCase(BaseModel):
    claim: str
    evidence: List[str]
    expected_status: str

class AggregateTestCase(BaseModel):
    projects: List[Dict[str, Any]]
    attribute: str
    target_value: str
    expected_count: int
    expected_percentage: float

# Benchmark dataset for query routing
ROUTER_BENCHMARK_DATA: List[RouterTestCase] = [
    RouterTestCase(
        query="What percentage of projects use LangGraph?",
        expected_type="aggregate",
        expected_attribute="frameworks",
        expected_value="LangGraph",
    ),
    RouterTestCase(
        query="How many repositories use FastAPI for backend APIs?",
        expected_type="aggregate",
        expected_attribute="frameworks",
        expected_value="FastAPI",
    ),
    RouterTestCase(
        query="Find projects implementing vector similarity search with ChromaDB.",
        expected_type="retrieve",
    ),
    RouterTestCase(
        query="Show me code snippets of multi-agent workflows.",
        expected_type="retrieve",
    ),
    RouterTestCase(
        query="Compare LangChain and AutoGen usage across the analyzed publications.",
        expected_type="compare",
    ),
    RouterTestCase(
        query="What is the weather today in New York?",
        expected_type="unsupported",
    ),
]

# Benchmark dataset for Fact-Checker Agent
FACT_CHECK_BENCHMARK_DATA: List[FactCheckTestCase] = [
    FactCheckTestCase(
        claim="2 out of 3 projects (66.7%) utilize LangChain.",
        evidence=[
            "Project A uses LangChain v0.2.0 in requirements.txt",
            "Project B imports langchain_core and langchain_community",
            "Project C uses purely native OpenAI SDK",
        ],
        expected_status="verified",
    ),
    FactCheckTestCase(
        claim="All analyzed repositories use PostgreSQL with pgvector.",
        evidence=[
            "Project A uses SQLite local storage",
            "Project B uses ChromaDB vector store",
            "Project C uses MongoDB",
        ],
        expected_status="unverified",
    ),
    FactCheckTestCase(
        claim="Project Alpha supports streaming responses.",
        evidence=[],
        expected_status="unverified",
    ),
]

# Benchmark dataset for Aggregation Calculations
AGGREGATE_BENCHMARK_DATA: List[AggregateTestCase] = [
    AggregateTestCase(
        projects=[
            {"project_name": "P1", "frameworks": [{"technology": "LangChain"}]},
            {"project_name": "P2", "frameworks": [{"technology": "LangChain"}, {"technology": "FastAPI"}]},
            {"project_name": "P3", "frameworks": [{"technology": "Streamlit"}]},
            {"project_name": "P4", "frameworks": [{"technology": "LangChain"}]},
        ],
        attribute="frameworks",
        target_value="LangChain",
        expected_count=3,
        expected_percentage=75.0,
    ),
    AggregateTestCase(
        projects=[
            {"project_name": "P1", "frameworks": [{"technology": "FastAPI"}]},
            {"project_name": "P2", "frameworks": [{"technology": "Flask"}]},
        ],
        attribute="frameworks",
        target_value="Django",
        expected_count=0,
        expected_percentage=0.0,
    ),
]
