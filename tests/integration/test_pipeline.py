"""Integration tests for the complete Chat with SQL pipeline."""

import pytest
import time
from unittest.mock import Mock, patch
from core.chat_with_sql import ChatWithSQLPipeline


@pytest.mark.integration
class TestChatPipeline:
    
    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance for testing."""
        return ChatWithSQLPipeline()
    
    @pytest.mark.integration
    @patch('core.chat_with_sql.ChatWithSQLPipeline._execute_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._generate_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._retrieve_schema')
    def test_full_question_processing(self, mock_retrieve, mock_generate, mock_execute, pipeline):
        """Test complete question processing pipeline with mocked components."""
        
        # Setup mocks
        mock_retrieve.return_value = [
            {
                "table": "users",
                "columns": ["id", "name", "email"],
                "description": "User accounts"
            }
        ]
        
        mock_generate.return_value = "SELECT * FROM users LIMIT 200"
        
        mock_execute.return_value = {
            "data": [
                {"id": 1, "name": "Test User", "email": "test@example.com"},
                {"id": 2, "name": "Another User", "email": "another@example.com"}
            ],
            "execution_time_ms": 150,
            "success": True
        }
        
        # Execute pipeline
        question = "Show all users"
        result = pipeline.chat_with_sql(question)
        
        # Verify response structure
        assert "answer" in result
        assert "sql" in result
        assert "explanation" in result
        assert "results" in result
        assert "metadata" in result
        
        # Verify SQL is what we generated
        assert result["sql"] == "SELECT * FROM users LIMIT 200"
        
        # Verify metadata
        assert result["metadata"]["sql_validated"] == True
        assert result["metadata"]["schema_retrieved"] == True
        assert result["metadata"]["execution_time_ms"] == 150
        
        # Verify results
        assert len(result["results"]) == 2
        assert result["results"][0]["name"] == "Test User"
    
    @pytest.mark.integration
    @patch('core.chat_with_sql.ChatWithSQLPipeline._execute_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._generate_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._retrieve_schema')
    def test_complex_query_processing(self, mock_retrieve, mock_generate, mock_execute, pipeline):
        """Test complex query with JOINs and aggregations."""
        
        # Setup mocks for complex query
        mock_retrieve.return_value = [
            {
                "table": "users",
                "columns": ["id", "name"],
                "description": "User accounts"
            },
            {
                "table": "tasks",
                "columns": ["id", "title", "assigned_to", "status"],
                "description": "Task management"
            }
        ]
        
        mock_generate.return_value = (
            "SELECT u.name, COUNT(t.id) as task_count "
            "FROM users u LEFT JOIN tasks t ON u.id = t.assigned_to "
            "GROUP BY u.id, u.name "
            "HAVING COUNT(t.id) > 3 "
            "LIMIT 200"
        )
        
        mock_execute.return_value = {
            "data": [
                {"name": "Active User", "task_count": 5},
                {"name": "Busy User", "task_count": 8}
            ],
            "execution_time_ms": 300,
            "success": True
        }
        
        # Execute complex query
        question = "Which users have more than 3 tasks?"
        result = pipeline.chat_with_sql(question)
        
        # Verify complex SQL
        assert "JOIN" in result["sql"].upper()
        assert "COUNT" in result["sql"].upper()
        assert "GROUP BY" in result["sql"].upper()
        assert "HAVING" in result["sql"].upper()
        
        # Verify results
        assert len(result["results"]) == 2
        assert all(result["task_count"] > 3 for result in result["results"])
    
    @pytest.mark.integration
    @patch('core.chat_with_sql.ChatWithSQLPipeline._validate_sql')
    def test_error_handling_invalid_sql(self, mock_validate, pipeline):
        """Test error handling for invalid SQL."""
        
        # Mock validation failure
        mock_validate.return_value = {
            "is_valid": False,
            "error": "SQL contains dangerous patterns",
            "risk_level": "HIGH"
        }
        
        # Test dangerous question
        dangerous_question = "Delete all users"
        result = pipeline.chat_with_sql(dangerous_question)
        
        # Verify error handling
        assert result["error"] is not None
        assert "dangerous" in result["error"].lower() or "not allowed" in result["error"].lower()
        assert result["sql"] is None  # No SQL should be generated
        assert result["results"] == []  # No results should be returned
    
    @pytest.mark.integration
    @patch('core.chat_with_sql.ChatWithSQLPipeline._execute_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._generate_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._retrieve_schema')
    def test_database_error_handling(self, mock_retrieve, mock_generate, mock_execute, pipeline):
        """Test handling of database execution errors."""
        
        # Setup mocks
        mock_retrieve.return_value = [{"table": "users", "columns": ["id", "name"]}]
        mock_generate.return_value = "SELECT * FROM users"
        
        # Mock database error
        mock_execute.return_value = {
            "data": [],
            "execution_time_ms": 1000,
            "success": False,
            "error": "Connection timeout"
        }
        
        # Execute query
        question = "Show all users"
        result = pipeline.chat_with_sql(question)
        
        # Verify error handling
        assert result["error"] is not None
        assert "timeout" in result["error"].lower()
        assert result["results"] == []
    
    @pytest.mark.integration
    @patch('core.chat_with_sql.ChatWithSQLPipeline._execute_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._generate_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._retrieve_schema')
    def test_empty_results_handling(self, mock_retrieve, mock_generate, mock_execute, pipeline):
        """Test handling of queries that return no results."""
        
        # Setup mocks
        mock_retrieve.return_value = [{"table": "users", "columns": ["id", "name"]}]
        mock_generate.return_value = "SELECT * FROM users WHERE name = 'Nonexistent'"
        
        # Mock empty results
        mock_execute.return_value = {
            "data": [],
            "execution_time_ms": 50,
            "success": True
        }
        
        # Execute query
        question = "Find user named Nonexistent"
        result = pipeline.chat_with_sql(question)
        
        # Verify empty results handling
        assert result["results"] == []
        assert result["error"] is None  # Empty results are not an error
        assert "no results" in result["answer"].lower() or "not found" in result["answer"].lower()
    
    @pytest.mark.integration
    @patch('core.chat_with_sql.ChatWithSQLPipeline._execute_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._generate_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._retrieve_schema')
    def test_large_result_set_handling(self, mock_retrieve, mock_generate, mock_execute, pipeline):
        """Test handling of large result sets."""
        
        # Setup mocks
        mock_retrieve.return_value = [{"table": "users", "columns": ["id", "name"]}]
        mock_generate.return_value = "SELECT * FROM users"
        
        # Mock large result set
        large_results = [
            {"id": i, "name": f"User {i}"}
            for i in range(1, 201)  # 200 results
        ]
        
        mock_execute.return_value = {
            "data": large_results,
            "execution_time_ms": 500,
            "success": True
        }
        
        # Execute query
        question = "Show all users"
        result = pipeline.chat_with_sql(question)
        
        # Verify large result handling
        assert len(result["results"]) == 200
        assert result["metadata"]["result_count"] == 200
        assert "LIMIT" in result["sql"].upper()  # Should have LIMIT clause
    
    @pytest.mark.integration
    @patch('core.chat_with_sql.ChatWithSQLPipeline._execute_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._generate_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._retrieve_schema')
    def test_performance_monitoring(self, mock_retrieve, mock_generate, mock_execute, pipeline):
        """Test performance monitoring and timing."""
        
        # Setup mocks with realistic timing
        mock_retrieve.return_value = [{"table": "users", "columns": ["id", "name"]}]
        mock_generate.return_value = "SELECT * FROM users"
        mock_execute.return_value = {
            "data": [{"id": 1, "name": "Test"}],
            "execution_time_ms": 250,
            "success": True
        }
        
        # Execute with timing
        start_time = time.time()
        question = "Show all users"
        result = pipeline.chat_with_sql(question)
        end_time = time.time()
        
        # Verify performance metrics
        total_time = (end_time - start_time) * 1000  # Convert to ms
        assert result["metadata"]["execution_time_ms"] == 250
        assert "total_time_ms" in result["metadata"]
        assert result["metadata"]["total_time_ms"] >= 250  # Should include all processing time
    
    @pytest.mark.integration
    def test_input_validation(self, pipeline):
        """Test input validation at pipeline level."""
        
        # Test empty question
        result = pipeline.chat_with_sql("")
        assert result["error"] is not None
        assert "empty" in result["error"].lower()
        
        # Test whitespace-only question
        result = pipeline.chat_with_sql("   ")
        assert result["error"] is not None
        assert "empty" in result["error"].lower()
        
        # Test too long question
        long_question = "test" * 200  # 800 characters
        result = pipeline.chat_with_sql(long_question)
        assert result["error"] is not None
        assert "too long" in result["error"].lower()
    
    @pytest.mark.integration
    @patch('core.chat_with_sql.ChatWithSQLPipeline._retrieve_schema')
    def test_schema_retrieval_failure(self, mock_retrieve, pipeline):
        """Test handling of schema retrieval failures."""
        
        # Mock schema retrieval failure
        mock_retrieve.side_effect = Exception("Schema retrieval failed")
        
        # Execute query
        question = "Show all users"
        result = pipeline.chat_with_sql(question)
        
        # Verify error handling
        assert result["error"] is not None
        assert "schema" in result["error"].lower()
    
    @pytest.mark.integration
    @patch('core.chat_with_sql.ChatWithSQLPipeline._generate_sql')
    @patch('core.chat_with_sql.ChatWithSQLPipeline._retrieve_schema')
    def test_sql_generation_failure(self, mock_retrieve, mock_generate, pipeline):
        """Test handling of SQL generation failures."""
        
        # Setup mocks
        mock_retrieve.return_value = [{"table": "users", "columns": ["id", "name"]}]
        
        # Mock SQL generation failure
        mock_generate.side_effect = Exception("SQL generation failed")
        
        # Execute query
        question = "Show all users"
        result = pipeline.chat_with_sql(question)
        
        # Verify error handling
        assert result["error"] is not None
        assert "sql generation" in result["error"].lower()
