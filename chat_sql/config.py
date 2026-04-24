"""
Configuration settings for Chat with SQL system.
Contains database connection, API keys, and model configurations.
"""

import os
from typing import Optional

class Config:
    """Configuration class for the Chat with SQL system."""
    
    # Database Configuration
    DB_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    DB_NAME: str = os.getenv("POSTGRES_DB", "chatdb")
    DB_USER: str = os.getenv("POSTGRES_USER", "postgres")
    DB_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "1234")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_LLM_MODEL: str = os.getenv("OLLAMA_LLM_MODEL", "gpt-oss:20b")
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    
    # Legacy OpenAI Configuration (kept for compatibility)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", OLLAMA_EMBED_MODEL)
    
    # Vector Store Configuration
    VECTOR_STORE_PATH: str = os.getenv("CHROMA_PERSIST_PATH", "./chroma_db")
    
    # RAG Configuration
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    
    # Safety Configuration
    MAX_RESULT_ROWS: int = int(os.getenv("MAX_ROWS", "200"))
    SQL_TIMEOUT_SECONDS: int = int(os.getenv("SQL_TIMEOUT_SECONDS", "30"))
    MAX_QUESTION_LENGTH: int = int(os.getenv("MAX_QUESTION_LENGTH", "500"))
    
    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def validate(self) -> None:
        """Validate required configuration."""
        # For Ollama setup, we don't require OpenAI API key
        # but we validate Ollama configuration
        if not self.OLLAMA_BASE_URL:
            raise ValueError("OLLAMA_BASE_URL is required")
        
        if not self.OLLAMA_LLM_MODEL:
            raise ValueError("OLLAMA_LLM_MODEL is required")
        
        if not self.DB_PASSWORD:
            raise ValueError("DB_PASSWORD is required")

# Global configuration instance
config = Config()
