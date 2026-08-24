import os
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings, get_chat_llm
import json

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
        """
        chain = self.prompt | self.llm | StrOutputParser()
        
        result = chain.invoke({
            "query": query,
            "structured_results": json.dumps(structured_results, indent=2),
            "fact_check": json.dumps(fact_check, indent=2)
        })
        
        return result
