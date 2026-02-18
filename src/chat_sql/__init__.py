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

from .core.chat_with_sql import ChatWithSQLPipeline
from .api.app import app

__all__ = [
    "ChatWithSQLPipeline",
    "app"
]
