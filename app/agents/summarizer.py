import os
import json
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings, get_chat_llm
from app.core.logging import get_logger
from app.core.exceptions import SummarizerError

logger = get_logger(__name__)


def load_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "summarizer.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


class SummarizerAgent:
    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm if llm is not None else get_chat_llm(temperature=0.3)
        self.system_prompt = load_prompt()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "Original Query: {query}\n\nStructured Results:\n{structured_results}\n\nFact-Check Verification:\n{fact_check}")
        ])

    def summarize(self, query: str, structured_results: Dict[str, Any], fact_check: Dict[str, Any]) -> str:
        """
        Produces a final natural language answer.
        Raises SummarizerError if the LLM call fails.
        """
        logger.info(
            "Summarising results",
            extra={"query_preview": query[:120], "fact_check_status": fact_check.get("status")},
        )

        chain = self.prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({
                "query": query,
                "structured_results": json.dumps(structured_results, indent=2),
                "fact_check": json.dumps(fact_check, indent=2),
            })
            logger.info(
                "Summarisation complete",
                extra={"answer_length": len(result)},
            )
            return result
        except Exception as e:
            raise SummarizerError(
                "Summariser LLM call failed",
                context={"query_preview": query[:120]},
                cause=e,
            ) from e
