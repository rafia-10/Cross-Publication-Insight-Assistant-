from pydantic import BaseModel, Field
from typing import List, Optional

class EvidenceItem(BaseModel):
    source: str = Field(..., description="File path or URL of the evidence")
    line_start: Optional[int] = Field(None, description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")
    text: str = Field(..., description="The exact text providing the evidence")

class TechnologyEvidence(BaseModel):
    technology: str = Field(..., description="Name of the technology or framework")
    category: str = Field(..., description="Category (e.g., agent_framework, vector_database)")
    evidence: Optional[EvidenceItem] = Field(None, description="Evidence supporting this technology usage")

class ProjectAnalysis(BaseModel):
    project_name: str = Field(..., description="Name of the project")
    source_type: str = Field(..., description="github or publication")
    source_url: str = Field(..., description="URL of the project source")
    description: Optional[str] = Field(None, description="Project description")
    
    frameworks: List[TechnologyEvidence] = Field(default_factory=list)
    agent_frameworks: List[TechnologyEvidence] = Field(default_factory=list)
    llms: List[TechnologyEvidence] = Field(default_factory=list)
    embedding_models: List[TechnologyEvidence] = Field(default_factory=list)
    vector_databases: List[TechnologyEvidence] = Field(default_factory=list)
    databases: List[TechnologyEvidence] = Field(default_factory=list)
    task_types: List[TechnologyEvidence] = Field(default_factory=list)
    architecture_patterns: List[TechnologyEvidence] = Field(default_factory=list)
    evaluation_methods: List[TechnologyEvidence] = Field(default_factory=list)
    deployment_tools: List[TechnologyEvidence] = Field(default_factory=list)
    protocols: List[TechnologyEvidence] = Field(default_factory=list)
    tools_used: List[TechnologyEvidence] = Field(default_factory=list)
    programming_languages: List[TechnologyEvidence] = Field(default_factory=list)
    
    uses_rag: bool = Field(False, description="Whether the project explicitly uses RAG")
    uses_agents: bool = Field(False, description="Whether the project explicitly uses autonomous agents")
    uses_mcp: bool = Field(False, description="Whether the project explicitly uses the MCP protocol")
