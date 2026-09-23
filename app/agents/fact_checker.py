import os
from typing import Optional, Any, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings, get_chat_llm
from app.core.logging import get_logger
from app.core.exceptions import FactCheckError

logger = get_logger(__name__)


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
        self.llm = llm if llm is not None else get_chat_llm(temperature=0)
        self.system_prompt = load_prompt()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "Claim: {claim}\n\nEvidence:\n{evidence}")
        ])

    def verify(self, claim: str, evidence: List[str]) -> FactCheckResult:
        """
        Verifies a claim against a list of evidence strings.
        Returns FactCheckResult with status='unverified' on LLM failure (graceful degradation).
        """
        if not evidence:
            logger.warning("Fact-check called with no evidence — returning unverified")
            return FactCheckResult(
                status="unverified",
                reasoning="No evidence provided to verify the claim.",
                supporting_evidence=[],
            )

        logger.info(
            "Fact-checking claim",
            extra={"claim_preview": claim[:120], "evidence_count": len(evidence)},
        )

        evidence_text = "\n\n---\n\n".join(evidence)
        chain = self.prompt | self.llm.with_structured_output(FactCheckResult)

        try:
            result = chain.invoke({"claim": claim, "evidence": evidence_text})
            logger.info(
                "Fact-check complete",
                extra={"status": result.status, "claim_preview": claim[:80]},
            )
            return result
        except Exception as e:
            logger.error(
                "Fact-checker LLM call failed — returning unverified",
                extra={"claim_preview": claim[:120]},
                exc_info=True,
            )
            # Graceful degradation: don't crash the pipeline
            return FactCheckResult(
                status="unverified",
                reasoning=f"Fact-check could not be completed due to an error: {e}",
                supporting_evidence=[],
            )
