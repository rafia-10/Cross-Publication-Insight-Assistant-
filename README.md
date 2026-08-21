# Cross-Publication Insight Assistant

A multi-agent AI system that allows users to provide a list of public GitHub repositories and/or Ready Tensor publications and then ask questions about patterns, trends, similarities, differences, and technologies across those projects.

## Architecture

Built with LangGraph, utilizing multiple agents:
- **Project Analyzer Agent**: Extracts structured data from repositories.
- **Query/Trend Agent**: Routes user queries (Aggregate, RAG, Compare).
- **Fact-Checker Agent**: Verifies claims against source evidence.
- **Summarizer Agent**: Formulates final natural language answers.

## Getting Started

1. Copy `.env.example` to `.env` and fill in your API keys.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run frontend/streamlit_app.py`
