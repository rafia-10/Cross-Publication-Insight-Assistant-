import os
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
import json

def load_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "summarizer.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

class SummarizerAgent:
    def __init__(self, llm: Optional[Any] = None):
        if not llm:
            api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.llm = ChatOpenAI(model="gpt-4o", api_key=api_key, temperature=0.3) # Slight temperature for natural phrasing
            else:
                self.llm = ChatOpenAI(model="gpt-4o", api_key="dummy", temperature=0.3)
        else:
            self.llm = llm
            
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
