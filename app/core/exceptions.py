"""
app.core.exceptions
~~~~~~~~~~~~~~~~~~~
Typed exception hierarchy for the Cross-Publication Insight Assistant.

All custom exceptions carry:
  - message  : human-readable description
  - context  : arbitrary dict of structured metadata for logging
  - cause    : the original exception that triggered this one (optional)
"""

from __future__ import annotations
from typing import Any, Dict, Optional


class InsightAssistantError(Exception):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context: Dict[str, Any] = context or {}
        self.cause = cause

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(message={self.message!r}, "
            f"context={self.context!r}, cause={self.cause!r})"
        )


# ---------------------------------------------------------------------------
# Ingestion errors
# ---------------------------------------------------------------------------

class IngestionError(InsightAssistantError):
    """Raised when any part of the ingestion pipeline fails."""


class FetchError(IngestionError):
    """Raised when a remote repository cannot be fetched / cloned."""


class ParseError(IngestionError):
    """Raised when a repository file cannot be read or parsed."""


class EmbeddingError(IngestionError):
    """Raised when vector embedding or storage fails."""


# ---------------------------------------------------------------------------
# Agent errors
# ---------------------------------------------------------------------------

class AgentError(InsightAssistantError):
    """Raised when an LLM agent call fails."""


class RoutingError(AgentError):
    """Raised when the query router LLM call fails."""


class AnalysisError(AgentError):
    """Raised when the project analyser agent fails."""


class FactCheckError(AgentError):
    """Raised when the fact-checker LLM call fails."""


class SummarizerError(AgentError):
    """Raised when the summariser LLM call fails."""


# ---------------------------------------------------------------------------
# Database errors
# ---------------------------------------------------------------------------

class DatabaseError(InsightAssistantError):
    """Raised when a SQL or vector-store operation fails."""
