"""
FastAPI application for Chat with SQL system.
Provides REST API endpoints for natural language to SQL conversion.
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from contextlib import asynccontextmanager

from ..core.chat_with_sql import chat_pipeline
from ..config import config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str
    
    class Config:
        schema_extra = {
            "example": {
                "question": "Which users have more than 3 tasks?"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    sql: str
    explanation: str
    results: List[Dict[str, Any]]
    warnings: List[str]
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str
    database_connected: bool
    schema_loaded: bool
    details: Dict[str, Any]


class SchemaStatsResponse(BaseModel):
    """Response model for schema statistics endpoint."""
    total_documents: int
    embedding_dimension: int
    model_name: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Chat with SQL API...")
    
    # Test database connection
    if not chat_pipeline.test_database_connection():
        logger.error("Failed to connect to database")
        raise RuntimeError("Database connection failed")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Chat with SQL API...")


# Create FastAPI app
app = FastAPI(
    title="Chat with SQL API",
    description="A RAG-based system for converting natural language questions to SQL queries",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chat with SQL API",
        "version": "1.0.0",
        "description": "Convert natural language questions to SQL queries using RAG"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status of the system
    """
    try:
        db_connected = chat_pipeline.test_database_connection()
        schema_stats = chat_pipeline.get_schema_stats()
        schema_loaded = schema_stats['total_documents'] > 0
        
        status_code = "healthy" if db_connected and schema_loaded else "unhealthy"
        
        return HealthResponse(
            status=status_code,
            database_connected=db_connected,
            schema_loaded=schema_loaded,
            details=schema_stats
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            schema_loaded=False,
            details={"error": str(e)}
        )


@app.post("/chat", response_model=ChatResponse)
async def chat_with_sql(request: ChatRequest):
    """
    Chat endpoint for natural language to SQL conversion.
    
    Args:
        request: Chat request with user question
        
    Returns:
        Chat response with answer, SQL, and metadata
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        # Process the question through the pipeline
        result = chat_pipeline.chat_with_sql(request.question)
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


@app.get("/schema/stats", response_model=SchemaStatsResponse)
async def get_schema_stats():
    """
    Get schema statistics.
    
    Returns:
        Schema statistics including document count and model info
    """
    try:
        stats = chat_pipeline.get_schema_stats()
        return SchemaStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Schema stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schema stats: {str(e)}"
        )


@app.post("/schema/refresh")
async def refresh_schema():
    """
    Refresh the schema information.
    
    Returns:
        Success message
    """
    try:
        chat_pipeline.refresh_schema()
        return {"message": "Schema refreshed successfully"}
    except Exception as e:
        logger.error(f"Schema refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh schema: {str(e)}"
        )


@app.get("/config")
async def get_config():
    """
    Get current configuration (non-sensitive).
    
    Returns:
        Current configuration settings
    """
    return {
        "ollama_base_url": config.OLLAMA_BASE_URL,
        "ollama_llm_model": config.OLLAMA_LLM_MODEL,
        "ollama_embed_model": config.OLLAMA_EMBED_MODEL,
        "embedding_model": config.EMBEDDING_MODEL,
        "top_k_retrieval": config.TOP_K_RETRIEVAL,
        "max_result_rows": config.MAX_RESULT_ROWS,
        "sql_timeout_seconds": config.SQL_TIMEOUT_SECONDS,
        "max_question_length": config.MAX_QUESTION_LENGTH,
        "db_host": config.DB_HOST,
        "db_port": config.DB_PORT,
        "db_name": config.DB_NAME
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
