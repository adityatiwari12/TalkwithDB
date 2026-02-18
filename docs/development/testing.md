# Testing Guide

## Overview

This guide covers the testing strategy for the Chat with SQL system, including unit tests, integration tests, and end-to-end testing. All tests are designed to ensure system reliability, security, and performance.

## Testing Philosophy

Our testing approach follows these principles:

1. **Test Early, Test Often**: Write tests alongside code development
2. **Comprehensive Coverage**: Test all critical paths and edge cases
3. **Fast Feedback**: Keep unit tests fast and integration tests focused
4. **Realistic Scenarios**: Use realistic data and query patterns
5. **Security First**: Test all security validations thoroughly

## Test Structure

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_sql_validator.py
│   ├── test_sql_generator.py
│   ├── test_embedder.py
│   ├── test_retriever.py
│   └── test_connection.py
├── integration/             # Component interaction tests
│   ├── test_pipeline.py
│   ├── test_api_endpoints.py
│   ├── test_schema_loader.py
│   └── test_safety_integration.py
├── e2e/                     # End-to-end tests
│   ├── test_full_workflow.py
│   └── test_api_client.py
├── fixtures/                # Test data and utilities
│   ├── sample_queries.py
│   ├── database_fixtures.py
│   └── mock_responses.py
└── conftest.py              # Pytest configuration
```

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_sql_validator.py

# Run specific test function
pytest tests/unit/test_sql_validator.py::test_select_only_validation

# Run with verbose output
pytest -v

# Run with specific markers
pytest -m unit
pytest -m integration
pytest -m slow
```

### Test Configuration

**pytest.ini**:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (database required)
    e2e: End-to-end tests (full system)
    slow: Tests that take more than 1 second
    security: Security-focused tests
```

## Unit Tests

### 1. SQL Validator Tests

**Location**: `tests/unit/test_sql_validator.py`

```python
import pytest
from safety.sql_validator import SQLValidator, ValidationResult

class TestSQLValidator:
    
    @pytest.fixture
    def validator(self):
        return SQLValidator()
    
    @pytest.mark.unit
    def test_select_only_validation(self, validator):
        """Test that only SELECT queries are allowed."""
        
        # Valid SELECT queries
        valid_queries = [
            "SELECT * FROM users",
            "SELECT name, email FROM users WHERE age > 18",
            "SELECT COUNT(*) FROM tasks"
        ]
        
        for query in valid_queries:
            result = validator.validate(query)
            assert result.is_valid, f"Query should be valid: {query}"
    
    @pytest.mark.unit
    def test_reject_dml_operations(self, validator):
        """Test that DML operations are rejected."""
        
        # Invalid queries
        invalid_queries = [
            "UPDATE users SET name = 'test'",
            "DELETE FROM users WHERE id = 1",
            "INSERT INTO users (name) VALUES ('test')",
            "DROP TABLE users"
        ]
        
        for query in invalid_queries:
            result = validator.validate(query)
            assert not result.is_valid, f"Query should be invalid: {query}"
            assert "not allowed" in result.error.lower()
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_sql_injection_detection(self, validator):
        """Test SQL injection pattern detection."""
        
        injection_queries = [
            "SELECT * FROM users WHERE name = 'admin' OR 1=1",
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM users WHERE name = 'test' --",
            "SELECT * FROM users UNION SELECT * FROM passwords"
        ]
        
        for query in injection_queries:
            result = validator.validate(query)
            assert not result.is_valid, f"Injection query should be rejected: {query}"
            assert result.risk_level in ["HIGH", "CRITICAL"]
    
    @pytest.mark.unit
    def test_system_table_protection(self, validator):
        """Test that system tables are protected."""
        
        system_table_queries = [
            "SELECT * FROM pg_user",
            "SELECT * FROM information_schema.tables",
            "SELECT * FROM mysql.user"
        ]
        
        for query in system_table_queries:
            result = validator.validate(query)
            assert not result.is_valid, f"System table access should be rejected: {query}"
```

### 2. SQL Generator Tests

**Location**: `tests/unit/test_sql_generator.py`

```python
import pytest
from unittest.mock import Mock, patch
from llm.sql_generator import SQLGenerator

class TestSQLGenerator:
    
    @pytest.fixture
    def generator(self):
        return SQLGenerator()
    
    @pytest.fixture
    def sample_schema(self):
        return [
            {
                "table": "users",
                "columns": ["id", "name", "email"],
                "description": "User accounts"
            },
            {
                "table": "tasks",
                "columns": ["id", "title", "assigned_to", "status"],
                "description": "Task management"
            }
        ]
    
    @pytest.mark.unit
    @patch('llm.sql_generator.SQLGenerator._call_ollama')
    def test_generate_simple_select(self, mock_ollama, generator, sample_schema):
        """Test simple SELECT query generation."""
        
        # Mock Ollama response
        mock_ollama.return_value = "SELECT * FROM users LIMIT 200"
        
        question = "Show all users"
        result = generator.generate_sql(question, sample_schema)
        
        assert "SELECT" in result.upper()
        assert "users" in result.lower()
        assert "LIMIT" in result.upper()
    
    @pytest.mark.unit
    @patch('llm.sql_generator.SQLGenerator._call_ollama')
    def test_generate_join_query(self, mock_ollama, generator, sample_schema):
        """Test JOIN query generation."""
        
        mock_ollama.return_value = (
            "SELECT u.name, t.title FROM users u "
            "JOIN tasks t ON u.id = t.assigned_to LIMIT 200"
        )
        
        question = "Show users and their tasks"
        result = generator.generate_sql(question, sample_schema)
        
        assert "JOIN" in result.upper()
        assert "users" in result.lower()
        assert "tasks" in result.lower()
    
    @pytest.mark.unit
    def test_prompt_construction(self, generator, sample_schema):
        """Test prompt construction with schema."""
        
        question = "Show all users"
        prompt = generator._construct_prompt(question, sample_schema)
        
        assert question in prompt
        assert "users" in prompt
        assert "tasks" in prompt
        assert "SELECT" in prompt.upper()
        assert "LIMIT" in prompt.upper()
```

### 3. Embedder Tests

**Location**: `tests/unit/test_embedder.py`

```python
import pytest
import numpy as np
from unittest.mock import Mock, patch
from rag.embedder import OllamaEmbedder

class TestOllamaEmbedder:
    
    @pytest.fixture
    def embedder(self):
        return OllamaEmbedder()
    
    @pytest.mark.unit
    @patch('rag.embedder.OllamaEmbedder._call_ollama')
    def test_text_embedding(self, mock_ollama, embedder):
        """Test text embedding generation."""
        
        # Mock embedding response
        mock_embedding = np.random.rand(768).tolist()
        mock_ollama.return_value = {"embedding": mock_embedding}
        
        text = "Show all users"
        result = embedder.embed(text)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 768
        mock_ollama.assert_called_once()
    
    @pytest.mark.unit
    def test_batch_embedding(self, embedder):
        """Test batch text embedding."""
        
        texts = ["Show users", "Find tasks", "List projects"]
        
        with patch.object(embedder, 'embed') as mock_embed:
            mock_embed.return_value = np.random.rand(768)
            
            results = embedder.embed_batch(texts)
            
            assert len(results) == 3
            assert mock_embed.call_count == 3
    
    @pytest.mark.unit
    def test_text_preprocessing(self, embedder):
        """Test text preprocessing."""
        
        # Test various text cleaning scenarios
        test_cases = [
            ("  Show users  ", "show users"),
            ("SHOW USERS!", "show users"),
            ("Show\nusers\tand\ntasks", "show users and tasks"),
            ("Show users... and tasks!", "show users and tasks")
        ]
        
        for input_text, expected_output in test_cases:
            result = embedder._preprocess_text(input_text)
            assert result == expected_output
```

## Integration Tests

### 1. Pipeline Integration Tests

**Location**: `tests/integration/test_pipeline.py`

```python
import pytest
from core.chat_with_sql import ChatWithSQLPipeline

@pytest.mark.integration
class TestChatPipeline:
    
    @pytest.fixture
    def pipeline(self):
        return ChatWithSQLPipeline()
    
    @pytest.mark.integration
    def test_full_question_processing(self, pipeline):
        """Test complete question processing pipeline."""
        
        question = "Show all users"
        result = pipeline.chat_with_sql(question)
        
        # Verify response structure
        assert "answer" in result
        assert "sql" in result
        assert "explanation" in result
        assert "results" in result
        assert "metadata" in result
        
        # Verify SQL is valid
        assert result["sql"].upper().startswith("SELECT")
        assert "LIMIT" in result["sql"].upper()
        
        # Verify metadata
        assert result["metadata"]["sql_validated"] == True
        assert result["metadata"]["schema_retrieved"] == True
    
    @pytest.mark.integration
    def test_complex_query_processing(self, pipeline):
        """Test complex query with JOINs."""
        
        question = "Which users have the most tasks?"
        result = pipeline.chat_with_sql(question)
        
        assert result["sql"].upper().count("JOIN") >= 1
        assert "COUNT" in result["sql"].upper()
        assert "GROUP BY" in result["sql"].upper()
    
    @pytest.mark.integration
    def test_error_handling(self, pipeline):
        """Test error handling for invalid questions."""
        
        # Test dangerous question
        dangerous_question = "Delete all users"
        result = pipeline.chat_with_sql(dangerous_question)
        
        assert result["error"] is not None
        assert "not allowed" in result["error"].lower()
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_performance_benchmarks(self, pipeline):
        """Test performance benchmarks."""
        
        import time
        
        questions = [
            "Show all users",
            "Count tasks by status",
            "List projects and their task counts"
        ]
        
        for question in questions:
            start_time = time.time()
            result = pipeline.chat_with_sql(question)
            end_time = time.time()
            
            # Should complete within 30 seconds
            assert (end_time - start_time) < 30.0
            assert result["metadata"]["execution_time_ms"] < 30000
```

### 2. API Integration Tests

**Location**: `tests/integration/test_api_endpoints.py`

```python
import pytest
from fastapi.testclient import TestClient
from api.app import app

@pytest.mark.integration
class TestAPIEndpoints:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.integration
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "database_connected" in data
        assert "schema_loaded" in data
    
    @pytest.mark.integration
    def test_chat_endpoint_success(self, client):
        """Test successful chat endpoint."""
        
        request_data = {"question": "Show all users"}
        response = client.post("/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sql" in data
        assert "results" in data
        assert data["error"] is None
    
    @pytest.mark.integration
    def test_chat_endpoint_validation(self, client):
        """Test chat endpoint input validation."""
        
        # Test empty question
        response = client.post("/chat", json={"question": ""})
        assert response.status_code == 400
        
        # Test missing question
        response = client.post("/chat", json={})
        assert response.status_code == 422
        
        # Test too long question
        long_question = "test" * 200
        response = client.post("/chat", json={"question": long_question})
        assert response.status_code == 400
    
    @pytest.mark.integration
    def test_schema_stats_endpoint(self, client):
        """Test schema statistics endpoint."""
        
        response = client.get("/schema/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_documents" in data
        assert "embedding_dimension" in data
        assert "model_name" in data
        assert data["total_documents"] > 0
```

## End-to-End Tests

### 1. Full Workflow Tests

**Location**: `tests/e2e/test_full_workflow.py`

```python
import pytest
import requests
import time

@pytest.mark.e2e
@pytest.mark.slow
class TestFullWorkflow:
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """Setup API client for E2E tests."""
        
        # Wait for server to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.BASE_URL}/health")
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("API server not ready after 30 seconds")
        
        yield requests
    
    @pytest.mark.e2e
    def test_complete_user_workflow(self, api_client):
        """Test complete user interaction workflow."""
        
        # Step 1: Check system health
        health_response = api_client.get(f"{self.BASE_URL}/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # Step 2: Check schema stats
        schema_response = api_client.get(f"{self.BASE_URL}/schema/stats")
        assert schema_response.status_code == 200
        assert schema_response.json()["total_documents"] > 0
        
        # Step 3: Ask simple question
        simple_response = api_client.post(
            f"{self.BASE_URL}/chat",
            json={"question": "Show all users"}
        )
        assert simple_response.status_code == 200
        simple_data = simple_response.json()
        assert len(simple_data["results"]) > 0
        
        # Step 4: Ask complex question
        complex_response = api_client.post(
            f"{self.BASE_URL}/chat",
            json={"question": "Which users have the most pending tasks?"}
        )
        assert complex_response.status_code == 200
        complex_data = complex_response.json()
        assert "JOIN" in complex_data["sql"].upper()
        
        # Step 5: Verify safety with dangerous query
        dangerous_response = api_client.post(
            f"{self.BASE_URL}/chat",
            json={"question": "Delete all users"}
        )
        assert dangerous_response.status_code == 200
        dangerous_data = dangerous_response.json()
        assert dangerous_data["error"] is not None
    
    @pytest.mark.e2e
    def test_concurrent_requests(self, api_client):
        """Test handling of concurrent requests."""
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(question):
            response = api_client.post(
                f"{self.BASE_URL}/chat",
                json={"question": question}
            )
            results.put(response.status_code == 200)
        
        # Make 5 concurrent requests
        threads = []
        questions = [
            "Show all users",
            "Count tasks by status",
            "List all projects",
            "Show user task assignments",
            "Find overdue tasks"
        ]
        
        for question in questions:
            thread = threading.Thread(target=make_request, args=(question,))
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        success_count = 0
        while not results.empty():
            if results.get():
                success_count += 1
        
        assert success_count == 5
```

## Test Fixtures and Utilities

### 1. Database Fixtures

**Location**: `tests/fixtures/database_fixtures.py`

```python
import pytest
import psycopg2
from contextlib import contextmanager

@pytest.fixture(scope="session")
def test_db_connection():
    """Setup test database connection."""
    
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "chatdb_test",
        "user": "chatuser",
        "password": "chatpass123"
    }
    
    # Create test database if it doesn't exist
    conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        database="postgres",
        user=db_config["user"],
        password=db_config["password"]
    )
    conn.autocommit = True
    
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE {db_config['database']}")
    
    conn.close()
    
    # Setup test data
    setup_test_data(db_config)
    
    yield db_config
    
    # Cleanup
    cleanup_test_data(db_config)

def setup_test_data(db_config):
    """Setup test data for tests."""
    
    conn = psycopg2.connect(**db_config)
    
    with conn.cursor() as cur:
        # Create test tables
        cur.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100)
            )
        """)
        
        cur.execute("""
            CREATE TABLE tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200),
                assigned_to INTEGER REFERENCES users(id),
                status VARCHAR(50)
            )
        """)
        
        # Insert test data
        cur.execute("""
            INSERT INTO users (name, email) VALUES
            ('Test User 1', 'test1@example.com'),
            ('Test User 2', 'test2@example.com'),
            ('Test User 3', 'test3@example.com')
        """)
        
        cur.execute("""
            INSERT INTO tasks (title, assigned_to, status) VALUES
            ('Task 1', 1, 'pending'),
            ('Task 2', 1, 'completed'),
            ('Task 3', 2, 'pending'),
            ('Task 4', 3, 'in_progress')
        """)
    
    conn.commit()
    conn.close()

def cleanup_test_data(db_config):
    """Clean up test data."""
    
    conn = psycopg2.connect(**db_config)
    
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS tasks")
        cur.execute("DROP TABLE IF EXISTS users")
    
    conn.commit()
    conn.close()
```

### 2. Mock Data

**Location**: `tests/fixtures/sample_queries.py`

```python
SAMPLE_QUERIES = {
    "simple_select": [
        "Show all users",
        "List all tasks",
        "Display all projects",
        "Get user information"
    ],
    
    "aggregate_queries": [
        "Count users by department",
        "How many tasks per user?",
        "Average tasks per project",
        "Total number of completed tasks"
    ],
    
    "join_queries": [
        "Show users and their tasks",
        "Which projects have pending tasks?",
        "List users with overdue tasks",
        "Find task assignments by project"
    ],
    
    "complex_queries": [
        "Which users have more than 5 tasks?",
        "Show projects with most overdue tasks",
        "Find users with no assigned tasks",
        "List completed tasks this month"
    ],
    
    "dangerous_queries": [
        "Delete all users",
        "DROP TABLE tasks",
        "UPDATE users SET name = 'hacked'",
        "SELECT * FROM pg_user"
    ]
}

EXPECTED_SQL_PATTERNS = {
    "simple_select": r"SELECT\s+\*\s+FROM\s+\w+",
    "aggregate_queries": r"SELECT\s+COUNT\(\*\)\s+FROM",
    "join_queries": r"SELECT.*JOIN.*ON",
    "complex_queries": r"SELECT.*HAVING.*COUNT"
}
```

## Performance Testing

### 1. Load Testing

**Location**: `tests/performance/test_load.py`

```python
import pytest
import time
import concurrent.futures
from statistics import mean, median

@pytest.mark.performance
@pytest.mark.slow
class TestLoadPerformance:
    
    @pytest.mark.performance
    def test_response_time_benchmarks(self, api_client):
        """Test response time benchmarks."""
        
        queries = [
            "Show all users",
            "Count tasks by status",
            "List projects and task counts"
        ]
        
        response_times = []
        
        for query in queries:
            start_time = time.time()
            response = api_client.post(
                "http://localhost:8000/chat",
                json={"question": query}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)
        
        # Performance assertions
        assert mean(response_times) < 5000  # Average < 5 seconds
        assert median(response_times) < 3000  # Median < 3 seconds
        assert max(response_times) < 10000  # Max < 10 seconds
    
    @pytest.mark.performance
    def test_concurrent_load(self, api_client):
        """Test system under concurrent load."""
        
        def make_request():
            start_time = time.time()
            response = api_client.post(
                "http://localhost:8000/chat",
                json={"question": "Show all users"}
            )
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": (end_time - start_time) * 1000
            }
        
        # Run 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        # Analyze results
        success_count = sum(1 for r in results if r["status_code"] == 200)
        response_times = [r["response_time"] for r in results]
        
        assert success_count >= 18  # At least 90% success rate
        assert mean(response_times) < 8000  # Average < 8 seconds under load
```

## Security Testing

### 1. Security Validation Tests

**Location**: `tests/security/test_sql_injection.py`

```python
import pytest
from safety.sql_validator import SQLValidator

@pytest.mark.security
class TestSQLInjectionSecurity:
    
    @pytest.fixture
    def validator(self):
        return SQLValidator()
    
    @pytest.mark.security
    def test_union_based_injection(self, validator):
        """Test UNION-based SQL injection detection."""
        
        injection_queries = [
            "SELECT * FROM users UNION SELECT * FROM passwords",
            "SELECT name FROM users UNION SELECT password FROM admin",
            "SELECT * FROM users WHERE id = 1 UNION SELECT * FROM sensitive_data"
        ]
        
        for query in injection_queries:
            result = validator.validate(query)
            assert not result.is_valid
            assert result.risk_level in ["HIGH", "CRITICAL"]
    
    @pytest.mark.security
    def test_boolean_based_injection(self, validator):
        """Test boolean-based SQL injection detection."""
        
        injection_queries = [
            "SELECT * FROM users WHERE name = 'admin' OR 1=1",
            "SELECT * FROM users WHERE id = 1 AND '1'='1'",
            "SELECT * FROM users WHERE name = 'test' OR 'x'='x'"
        ]
        
        for query in injection_queries:
            result = validator.validate(query)
            assert not result.is_valid
            assert "injection" in result.error.lower()
    
    @pytest.mark.security
    def test_time_based_injection(self, validator):
        """Test time-based SQL injection detection."""
        
        injection_queries = [
            "SELECT * FROM users WHERE name = 'test' AND (SELECT * FROM (SELECT(SLEEP(5)))a)",
            "SELECT * FROM users WHERE name = 'test' AND pg_sleep(5)",
            "SELECT * FROM users WHERE name = 'test' WAITFOR DELAY '00:00:05'"
        ]
        
        for query in injection_queries:
            result = validator.validate(query)
            assert not result.is_valid
            assert "suspicious" in result.error.lower()
```

## Continuous Integration

### 1. GitHub Actions Workflow

**Location**: `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: chatdb_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r src/chat_sql/requirements.txt
        pip install pytest pytest-cov black flake8
    
    - name: Run linting
      run: |
        black --check src/
        flake8 src/
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src/
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
      env:
        POSTGRES_HOST: localhost
        POSTGRES_DB: chatdb_test
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: postgres
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Best Practices

### 1. Test Writing Guidelines

- **Descriptive Names**: Use clear, descriptive test names
- **AAA Pattern**: Arrange, Act, Assert structure
- **Single Assertion**: One assertion per test when possible
- **Test Data**: Use fixtures for consistent test data
- **Mock External Services**: Mock Ollama, database, etc. in unit tests

### 2. Test Data Management

- **Isolation**: Each test should be independent
- **Cleanup**: Clean up test data after each test
- **Realistic Data**: Use realistic but anonymized data
- **Edge Cases**: Test boundary conditions and error cases

### 3. Performance Considerations

- **Fast Unit Tests**: Keep unit tests under 1 second
- **Parallel Execution**: Run tests in parallel when possible
- **Resource Management**: Properly manage database connections
- **Memory Usage**: Clean up large objects in tests

## Troubleshooting

### Common Test Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection parameters
   - Ensure test database exists

2. **Ollama Connection Failed**
   - Mock Ollama in unit tests
   - Start Ollama service for integration tests
   - Check model availability

3. **Test Timeouts**
   - Increase timeout for slow tests
   - Optimize test queries
   - Use async test patterns

4. **Flaky Tests**
   - Add proper cleanup
   - Remove test dependencies
   - Use deterministic test data

This comprehensive testing strategy ensures the Chat with SQL system is reliable, secure, and performs well under various conditions.
