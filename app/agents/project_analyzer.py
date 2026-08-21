import os
from typing import Optional, Dict, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from app.schemas.project import ProjectAnalysis
from app.tools.repository_search import search_repository
from app.config import settings

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
        if not llm:
            api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
            # If no API key is provided, we can still instantiate the class for testing, but it will fail on invoke
            if api_key:
                self.llm = ChatOpenAI(model="gpt-4o", api_key=api_key, temperature=0)
            else:
                self.llm = ChatOpenAI(model="gpt-4o", api_key="dummy_key", temperature=0) # For mocked tests
        else:
            self.llm = llm
            
        self.system_prompt = load_prompt()

    def analyze(self, repo_path: str, project_name: str, source_url: str, source_type: str = "github") -> ProjectAnalysis:
        """
        Analyzes a repository and extracts structured metadata.
        """
        search_tool = create_search_tool(repo_path)
        
        # We use create_react_agent from langgraph.prebuilt
        # To enforce structured output, we can use the response_format feature if using OpenAI
        
        llm_with_structured_output = self.llm.bind_tools([search_tool])
        
        agent = create_react_agent(
            model=self.llm,
            tools=[search_tool],
            state_modifier=self.system_prompt,
            response_format=ProjectAnalysis
        )
        
        # Initial instruction
        initial_message = (
            f"Analyze the project '{project_name}' located at '{repo_path}'. "
            f"Source URL: {source_url}. Source Type: {source_type}. "
            "Please explore the repository using the search tool, find evidence for technologies used, "
            "and output the final ProjectAnalysis data."
        )
        
        result = agent.invoke({"messages": [("user", initial_message)]})
        
        # The response_format parameter in create_react_agent forces the final message to be the structured output.
        # It's returned as the 'structured_response' key in the output state, or parsed from the final message.
        if "structured_response" in result:
            return result["structured_response"]
            
        # Fallback if structured_response isn't automatically parsed
        final_msg = result["messages"][-1]
        
        # If the LLM failed to return structured data directly, we might need a fallback parse
        # But create_react_agent with response_format should handle it.
        # For safety, returning a default empty analysis if parsing fails
        return ProjectAnalysis(
            project_name=project_name,
            source_url=source_url,
            source_type=source_type,
            description="Analysis failed to return structured data."
        )
