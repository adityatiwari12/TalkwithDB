"""
Chat with SQL - RAG-Based Natural Language to SQL System

A production-style prototype that converts natural language questions into safe SQL queries 
using Retrieval-Augmented Generation (RAG) with Ollama for local LLM processing.

This package provides:
- Natural language to SQL conversion
- RAG-based schema retrieval
- SQL safety validation
- Local LLM processing with Ollama
- REST API interface
"""

__version__ = "1.0.0"
__author__ = "Chat SQL Team"
__description__ = "RAG-based Natural Language to SQL System"

__all__ = ["ChatWithSQLPipeline", "app"]


def __getattr__(name: str):
    """
    Lazily import heavy modules to avoid side effects on package import.

    Some runtime environments may block native DB drivers (e.g., psycopg2 DLL),
    so importing core/api eagerly can fail even when those paths are unused.
    """
    if name == "ChatWithSQLPipeline":
        from .core.chat_with_sql import ChatWithSQLPipeline

        return ChatWithSQLPipeline
    if name == "app":
        from .api.app import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
