import os
from typing import Optional, Dict, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from app.schemas.project import ProjectAnalysis
from app.tools.repository_search import search_repository
from app.config import settings, get_chat_llm
from app.core.logging import get_logger
from app.core.exceptions import AnalysisError

logger = get_logger(__name__)


def load_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "project_analyzer.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def create_search_tool(repo_path: str):
    @tool
    def search_repo_tool(query: str) -> str:
        """Search the repository files for a specific keyword or query to find evidence of technologies."""
        results = search_repository(repo_path, query, max_results=5)
        if not results:
            return "No results found."

        output = []
        for r in results:
            output.append(f"File: {r.file_path}, Line: {r.line_number}\nSnippet:\n{r.content_snippet}\n---")
        return "\n".join(output)
    return search_repo_tool


class ProjectAnalyzer:
    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm if llm is not None else get_chat_llm(temperature=0)
        self.system_prompt = load_prompt()

    def analyze(self, repo_path: str, project_name: str, source_url: str, source_type: str = "github") -> ProjectAnalysis:
        """
        Analyzes a repository and extracts structured metadata.
        Raises AnalysisError if the agent fails to produce a valid result.
        """
        logger.info(
            "Starting project analysis",
            extra={"project_name": project_name, "source_url": source_url, "source_type": source_type},
        )

        search_tool = create_search_tool(repo_path)

        # We use create_react_agent from langgraph.prebuilt
        # To enforce structured output, we can use the response_format feature if using OpenAI
        agent = create_react_agent(
            model=self.llm,
            tools=[search_tool],
            state_modifier=self.system_prompt,
            response_format=ProjectAnalysis,
        )

        # Initial instruction
        initial_message = (
            f"Analyze the project '{project_name}' located at '{repo_path}'. "
            f"Source URL: {source_url}. Source Type: {source_type}. "
            "Please explore the repository using the search tool, find evidence for technologies used, "
            "and output the final ProjectAnalysis data."
        )

        try:
            result = agent.invoke({"messages": [("user", initial_message)]})
        except Exception as e:
            raise AnalysisError(
                f"Project analyser agent failed for '{project_name}'",
                context={"project_name": project_name, "source_url": source_url},
                cause=e,
            ) from e

        # The response_format parameter in create_react_agent forces the final message to be the structured output.
        # It's returned as the 'structured_response' key in the output state, or parsed from the final message.
        if "structured_response" in result:
            logger.info(
                "Project analysis complete",
                extra={"project_name": project_name},
            )
            return result["structured_response"]

        # Fallback if structured_response isn't automatically parsed
        logger.warning(
            "Project analyser did not return structured_response — using default fallback",
            extra={"project_name": project_name},
        )
        return ProjectAnalysis(
            project_name=project_name,
            source_url=source_url,
            source_type=source_type,
            description="Analysis failed to return structured data.",
        )
