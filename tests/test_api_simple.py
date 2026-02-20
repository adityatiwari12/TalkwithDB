"""
Simple API test for Version 3
Tests all endpoints without complex dependencies
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

app = FastAPI(
    title="Talk with DB - Version 3 (Test)",
    description="Simplified API for testing connectivity",
    version="3.0.0-test"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    max_tables: int = 3

class ChatResponse(BaseModel):
    content: str
    sql_query: Optional[str] = None
    results: Optional[List[Dict]] = None
    session_id: str
    metadata: Dict[str, Any]

@app.get("/")
async def root():
    return {
        "name": "Talk with DB API - Version 3 (Test Mode)",
        "version": "3.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "connected",
            "database": "not_tested",
            "ollama": "not_tested"
        }
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Test chat endpoint - returns mock response"""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Mock response for testing
    return ChatResponse(
        content=f"Test response for: '{request.message}'. Full RAG pipeline not loaded in test mode.",
        sql_query="SELECT * FROM test_table LIMIT 5;",
        results=[{"id": 1, "name": "Test"}, {"id": 2, "name": "Test 2"}],
        session_id=session_id,
        metadata={
            "test_mode": True,
            "message": request.message,
            "max_tables": request.max_tables
        }
    )

@app.get("/api/schema")
async def get_schema():
    """Test schema endpoint"""
    return {
        "tables": [
            {"table_name": "users", "columns": [{"name": "id", "type": "INTEGER"}]},
            {"table_name": "orders", "columns": [{"name": "id", "type": "INTEGER"}]}
        ],
        "total_tables": 2
    }

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Test history endpoint"""
    return {
        "session_id": session_id,
        "turns": [],
        "referenced_tables": []
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting TEST API server...")
    print("📡 API will be available at: http://localhost:8002")
    print("📚 Docs available at: http://localhost:8002/docs")
    uvicorn.run(app, host="0.0.0.0", port=8002)
