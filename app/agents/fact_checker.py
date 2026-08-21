import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings

class FactCheckResult(BaseModel):
    status: str = Field(..., description="One of: verified, partial, unverified")
    reasoning: str = Field(..., description="Explanation of the decision")
    supporting_evidence: List[str] = Field(default_factory=list, description="Specific snippets supporting the claim")

def load_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "fact_checker.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

class FactCheckerAgent:
    def __init__(self, llm: Optional[Any] = None):
        if not llm:
            api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.llm = ChatOpenAI(model="gpt-4o", api_key=api_key, temperature=0)
            else:
                self.llm = ChatOpenAI(model="gpt-4o", api_key="dummy", temperature=0)
        else:
            self.llm = llm
            
        self.system_prompt = load_prompt()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "Claim: {claim}\n\nEvidence:\n{evidence}")
        ])
        
    def verify(self, claim: str, evidence: List[str]) -> FactCheckResult:
        """
        Verifies a claim against a list of evidence strings.
        """
        if not evidence:
            return FactCheckResult(
                status="unverified",
                reasoning="No evidence provided to verify the claim.",
                supporting_evidence=[]
            )
            
        evidence_text = "\n\n---\n\n".join(evidence)
        chain = self.prompt | self.llm.with_structured_output(FactCheckResult)
        
        result = chain.invoke({
            "claim": claim,
            "evidence": evidence_text
        })
        
        return result
