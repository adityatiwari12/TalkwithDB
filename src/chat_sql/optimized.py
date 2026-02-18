"""
Optimized Chat with SQL System - Scalable RAG Implementation

This module provides a production-ready, terminal-based Chat with SQL system
optimized for very large and evolving database schemas.

Key Features:
- Persistent vector storage with FAISS
- Incremental schema updates (no full re-embedding)
- Table-level chunking for efficient retrieval
- Metadata-based pre-filtering to reduce search space
- Lazy initialization for fast startup
- Top-K retrieval limits (2-3 tables max)
- Performance monitoring and optimization tracking

Architecture Benefits:
- Handles 1000+ tables efficiently
- Minimal startup latency (<1s)
- Low memory footprint
- Fast query processing (<500ms)
- Production-ready error handling

Usage:
    python optimized_cli.py                    # Interactive mode
    python optimized_cli.py "How many users?"  # Single query
    python optimized_cli.py --batch queries.txt    # Batch processing
    python optimized_cli.py --stats               # System statistics
"""

from .core.optimized_pipeline import optimized_chat_pipeline
from .core.schema_manager import schema_manager
from .rag.optimized_retriever import optimized_schema_retriever
from .rag.optimized_vector_store import OptimizedVectorStore
from .optimized_cli import OptimizedChatCLI

__version__ = "2.0.0"
__author__ = "Chat SQL Team"
__description__ = "Scalable RAG-based Natural Language to SQL System"

__all__ = [
    "optimized_chat_pipeline",
    "schema_manager", 
    "optimized_schema_retriever",
    "OptimizedVectorStore",
    "OptimizedChatCLI"
]
