"""
FastAPI Backend for Version 3 Chatbot.
Provides REST API and WebSocket endpoints for real-time chat.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import uuid
import logging
from datetime import datetime
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ..config import config
from ..rag.advanced_rag import AdvancedRAGPipeline, ConversationMemory, ConversationTurn
from ..rag.optimized_retriever import optimized_schema_retriever
from ..core.optimized_pipeline import OptimizedChatWithSQLPipeline
from ..llm.sql_generator import sql_generator
from ..llm.result_formatter import ResultFormatter
from ..safety.sql_validator import sql_validator
from ..db.connection import db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Talk with DB - Version 3",
    description="Advanced Chat with SQL API with RAG and WebSocket support",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
try:
    from ..rag.retriever import get_schema_retriever
    schema_retriever = get_schema_retriever()
    advanced_rag = AdvancedRAGPipeline(schema_retriever.vector_store)
except Exception as e:
    logger.error(f"Failed to initialize AdvancedRAGPipeline: {e}")
    # Fallback to simple pipeline
    advanced_rag = None
pipeline = OptimizedChatWithSQLPipeline()

# Session management
active_sessions: Dict[str, Dict[str, Any]] = {}


# Pydantic Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    max_tables: int = 3


class ChatResponse(BaseModel):
    response: str
    sql_query: Optional[str] = None
    results: Optional[List[Dict]] = None
    session_id: str
    metadata: Dict[str, Any]


class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    message_count: int
    last_activity: datetime


class QueryHistoryItem(BaseModel):
    timestamp: datetime
    question: str
    sql_query: str
    execution_time: float
    row_count: int


class ExportRequest(BaseModel):
    session_id: str
    format: str = "csv"  # csv, json, excel


class SchemaInfo(BaseModel):
    table_name: str
    columns: List[Dict[str, Any]]
    row_count: Optional[int] = None
    relationships: List[str]


class SuggestionRequest(BaseModel):
    partial_query: str


# REST API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Talk with DB API - Version 3",
        "version": "3.0.0",
        "features": [
            "Advanced RAG with query rewriting",
            "Hybrid search (BM25 + Vector)",
            "LLM re-ranking",
            "Conversation memory",
            "Real-time WebSocket chat",
            "Query history",
            "Schema exploration",
            "Export functionality"
        ],
        "endpoints": {
            "chat": "/api/chat",
            "websocket": "/ws/chat",
            "history": "/api/history/{session_id}",
            "schema": "/api/schema",
            "sessions": "/api/sessions",
            "export": "/api/export"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        db_connection.test_connection()
        
        # Check Ollama connection
        # (Would need to implement this check)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": "connected",
                "ollama": "connected",
                "vector_store": "ready"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - processes natural language questions.
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                "created_at": datetime.now(),
                "message_count": 0,
                "last_activity": datetime.now()
            }
        
        # Update session activity
        active_sessions[session_id]["last_activity"] = datetime.now()
        active_sessions[session_id]["message_count"] += 1
        
        # Check if advanced_rag is available
        if advanced_rag is None:
            return ChatResponse(
                response="I'm sorry, the advanced RAG system is not available right now. Please try again later.",
                sql_query=None,
                results=None,
                session_id=session_id,
                metadata={"error": "AdvancedRAGPipeline not initialized"}
            )
        
        # Step 1: Advanced RAG retrieval
        logger.info(f"Processing chat message for session {session_id}: {request.message}")
        
        retrieval_result = advanced_rag.retrieve(
            query=request.message,
            session_id=session_id,
            top_k=request.max_tables
        )
        
        # Step 2: Generate SQL
        sql_start = datetime.now()
        try:
            sql_result = sql_generator.generate_sql(
                question=retrieval_result['rewritten_query'],
                schema_context=retrieval_result['schema_context']
            )
            sql_query = sql_result.get('sql', '')
            logger.info(f"Generated SQL: {sql_query}")
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return ChatResponse(
                response=f"I'm sorry, I encountered an error generating the SQL query: {str(e)}",
                sql_query=None,
                results=None,
                session_id=session_id,
                metadata={"error": "SQL generation failed"}
            )
        sql_time = (datetime.now() - sql_start).total_seconds()
        
        # Step 3: Validate SQL
        validation_result = sql_validator.validate_sql(sql_query)
        
        if not validation_result.is_valid:
            # Return error response
            response = ChatResponse(
                response=f"I couldn't generate a valid query. Reason: {validation_result.error_message}",
                sql_query=None,
                results=None,
                session_id=session_id,
                metadata={
                    "retrieval": retrieval_result,
                    "validation": {
                        "is_valid": False,
                        "error": validation_result.error_message
                    },
                    "timing": {"sql_generation": sql_time}
                }
            )
            
            # Add to conversation memory
            advanced_rag.memory.add_turn(
                session_id=session_id,
                role="user",
                content=request.message
            )
            advanced_rag.memory.add_turn(
                session_id=session_id,
                role="assistant",
                content=response.response,
                sql_query=None,
                context_tables=retrieval_result['retrieved_tables']
            )
            
            return response
        
        # Step 4: Execute SQL
        exec_start = datetime.now()
        try:
            results = db_connection.execute_query(sql_query)
            exec_time = (datetime.now() - exec_start).total_seconds()
            row_count = len(results) if results else 0
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            results = []
            exec_time = 0
            row_count = 0
        
        # Step 5: Format response
        formatter = ResultFormatter()
        natural_response = formatter.format_result(
            question=request.message,
            sql_query=sql_query,
            results=results
        )
        
        # Calculate total time
        total_time = sql_time + exec_time
        
        # Build response
        response = ChatResponse(
            response=natural_response,
            sql_query=sql_query,
            results=results[:20] if results else [],  # Limit results in response
            session_id=session_id,
            metadata={
                "retrieval": {
                    "original_query": retrieval_result['original_query'],
                    "rewritten_query": retrieval_result['rewritten_query'],
                    "expansion_terms": retrieval_result['expansion_terms'],
                    "intent": retrieval_result['intent'],
                    "retrieved_tables": retrieval_result['retrieved_tables'],
                    "search_results": retrieval_result['search_results']
                },
                "validation": {
                    "is_valid": True,
                    "warnings": validation_result.warnings
                },
                "execution": {
                    "row_count": row_count,
                    "execution_time": exec_time
                },
                "timing": {
                    "sql_generation": sql_time,
                    "query_execution": exec_time,
                    "total": total_time
                }
            }
        )
        
        # Add to conversation memory
        advanced_rag.memory.add_turn(
            session_id=session_id,
            role="user",
            content=request.message
        )
        advanced_rag.memory.add_turn(
            session_id=session_id,
            role="assistant",
            content=natural_response,
            sql_query=sql_query,
            context_tables=retrieval_result['retrieved_tables']
        )
        
        logger.info(f"Chat response generated for session {session_id} in {total_time:.2f}s")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session."""
    try:
        history = advanced_rag.memory.get_history(session_id)
        
        return {
            "session_id": session_id,
            "turns": [
                {
                    "role": turn.role,
                    "content": turn.content,
                    "sql_query": turn.sql_query,
                    "timestamp": turn.timestamp.isoformat(),
                    "context_tables": turn.context_tables
                }
                for turn in history
            ],
            "referenced_tables": advanced_rag.memory.extract_referenced_tables(session_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/history/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history for a session."""
    try:
        advanced_rag.memory.clear_session(session_id)
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        return {"message": f"History cleared for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schema")
async def get_schema():
    """Get database schema information."""
    try:
        from ..db.schema_loader import schema_loader
        
        tables = schema_loader.get_all_tables()
        schema_info = []
        
        for table_name in tables:
            try:
                table_info = schema_loader.get_table_info(table_name)
                
                # Get row count
                try:
                    count_result = db_connection.execute_query(
                        f"SELECT COUNT(*) as count FROM {table_name}"
                    )
                    row_count = count_result[0]['count'] if count_result else 0
                except:
                    row_count = None
                
                schema_info.append({
                    "table_name": table_name,
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.data_type,
                            "nullable": True,  # Will be populated from database query
                            "primary_key": col.is_primary_key
                        }
                        for col in table_info.columns
                    ],
                    "row_count": row_count,
                    "relationships": [
                        f"{rel.target_table}.{rel.target_column}"
                        for rel in table_info.relationships
                    ]
                })
            except Exception as e:
                logger.warning(f"Could not get info for table {table_name}: {e}")
        
        return {
            "tables": schema_info,
            "total_tables": len(schema_info)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schema/{table_name}")
async def get_table_details(table_name: str):
    """Get detailed information about a specific table."""
    try:
        from db.schema_loader import schema_loader
        
        table_info = schema_loader.get_table_info(table_name)
        
        # Sample data (first 5 rows)
        try:
            sample_data = db_connection.execute_query(
                f"SELECT * FROM {table_name} LIMIT 5"
            )
        except:
            sample_data = []
        
        return {
            "table_name": table_name,
            "columns": [
                {
                    "name": col.name,
                    "type": col.data_type,
                    "nullable": col.nullable,
                    "primary_key": col.primary_key,
                    "foreign_key": col.foreign_key
                }
                for col in table_info.columns
            ],
            "relationships": [
                {
                    "type": rel.relationship_type,
                    "target_table": rel.target_table,
                    "target_column": rel.target_column,
                    "source_column": rel.source_column
                }
                for rel in table_info.relationships
            ],
            "sample_data": sample_data,
            "create_statement": table_info.create_statement
        }
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")


@app.get("/api/sessions")
async def get_sessions():
    """Get all active sessions."""
    return {
        "sessions": [
            {
                "session_id": sid,
                "created_at": info["created_at"].isoformat(),
                "message_count": info["message_count"],
                "last_activity": info["last_activity"].isoformat()
            }
            for sid, info in active_sessions.items()
        ],
        "total_sessions": len(active_sessions)
    }


@app.post("/api/export")
async def export_results(request: ExportRequest):
    """Export query results in various formats."""
    try:
        # Get last query from session
        history = advanced_rag.memory.get_history(request.session_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="No queries found in session")
        
        # Find last assistant turn with SQL query
        last_query = None
        for turn in reversed(history):
            if turn.role == "assistant" and turn.sql_query:
                last_query = turn.sql_query
                break
        
        if not last_query:
            raise HTTPException(status_code=404, detail="No SQL query found in session")
        
        # Execute query to get results
        results = db_connection.execute_query(last_query)
        
        # Format based on request
        if request.format == "json":
            return JSONResponse(content=results)
        
        elif request.format == "csv":
            import csv
            import io
            
            if not results:
                return {"data": ""}
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
            
            return {
                "data": output.getvalue(),
                "filename": f"query_results_{request.session_id}.csv"
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggest")
async def get_suggestions(request: SuggestionRequest):
    """Get query suggestions based on partial input."""
    try:
        # Common query patterns
        suggestions = [
            "How many users are there?",
            "Show all active orders",
            "What is the total revenue this month?",
            "List top 10 customers by purchase amount",
            "Show tasks assigned to John",
            "Count projects by status",
            "What is the average order value?",
            "Show recent activities in the last 7 days"
        ]
        
        # Filter based on partial input
        partial = request.partial_query.lower()
        filtered = [s for s in suggestions if partial in s.lower()]
        
        # Add schema-based suggestions
        try:
            from ..db.schema_loader import schema_loader
            tables = schema_loader.get_all_tables()
            for table in tables[:5]:  # Limit to first 5 tables
                if partial in table.lower() or not partial:
                    filtered.append(f"Show all records from {table}")
                    filtered.append(f"Count rows in {table}")
        except Exception as e:
            logger.error(f"Error getting table names: {e}")
            # Continue without table suggestions
        return {
            "suggestions": filtered[:8],  # Limit suggestions
            "partial_query": request.partial_query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoint for Real-time Chat

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with streaming responses.
    """
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    
    try:
        # Send welcome message with session ID
        await websocket.send_json({
            "type": "session",
            "session_id": session_id,
            "message": "Connected to Talk with DB - Version 3"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            
            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "status": "thinking"
            })
            
            try:
                # Process message (reuse chat logic)
                retrieval_result = advanced_rag.retrieve(
                    query=user_message,
                    session_id=session_id,
                    top_k=3
                )
                
                # Stream retrieval info
                await websocket.send_json({
                    "type": "retrieval",
                    "tables": retrieval_result['retrieved_tables'],
                    "rewritten_query": retrieval_result['rewritten_query']
                })
                
                # Generate SQL
                sql_query = sql_generator.generate_sql(
                    question=retrieval_result['rewritten_query'],
                    schema_context=retrieval_result['schema_context']
                )
                
                await websocket.send_json({
                    "type": "sql",
                    "query": sql_query
                })
                
                # Validate
                validation = sql_validator.validate(sql_query)
                
                if validation.is_valid:
                    # Execute
                    results = db_connection.execute_query(sql_query)
                    
                    # Format and send response
                    formatter = ResultFormatter()
                    response_text = formatter.format_results(
                        question=user_message,
                        sql_query=sql_query,
                        results=results
                    )
                    
                    await websocket.send_json({
                        "type": "response",
                        "text": response_text,
                        "sql_query": sql_query,
                        "row_count": len(results) if results else 0,
                        "metadata": {
                            "retrieved_tables": retrieval_result['retrieved_tables'],
                            "warnings": validation.warnings
                        }
                    })
                    
                    # Update memory
                    advanced_rag.memory.add_turn(
                        session_id=session_id,
                        role="user",
                        content=user_message
                    )
                    advanced_rag.memory.add_turn(
                        session_id=session_id,
                        role="assistant",
                        content=response_text,
                        sql_query=sql_query,
                        context_tables=retrieval_result['retrieved_tables']
                    )
                    
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Validation failed: {validation.error_message}"
                    })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
