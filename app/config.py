import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o"
    openrouter_embedding_model: str = "text-embedding-3-small"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    
    database_url: str = "sqlite:///./insight.db"
    chroma_persist_directory: str = "./chroma_data"

    # Logging configuration
    log_level: str = "INFO"   # DEBUG | INFO | WARNING | ERROR
    log_format: str = "json"  # json | text

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

def get_chat_llm(model: Optional[str] = None, temperature: float = 0) -> ChatOpenAI:
    api_key = settings.openrouter_api_key or os.environ.get("OPENROUTER_API_KEY") or settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
    selected_model = model or settings.openrouter_model or "openai/gpt-4o"
    
    if api_key:
        is_openrouter = bool(settings.openrouter_api_key or os.environ.get("OPENROUTER_API_KEY"))
        base_url = settings.openrouter_base_url if is_openrouter else None
        
        headers = {}
        if is_openrouter:
            headers = {
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Insight-Assistant"
            }
            
        return ChatOpenAI(
            model=selected_model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            default_headers=headers if headers else None
        )
    return ChatOpenAI(model=selected_model, api_key="dummy_key", temperature=temperature)

