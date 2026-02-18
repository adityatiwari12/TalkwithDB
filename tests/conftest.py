"""Pytest configuration and shared fixtures."""

import pytest
import os
import sys
from unittest.mock import Mock, MagicMock

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'chat_sql'))

# Set test environment variables
os.environ.update({
    'POSTGRES_HOST': 'localhost',
    'POSTGRES_DB': 'chatdb_test',
    'POSTGRES_USER': 'testuser',
    'POSTGRES_PASSWORD': 'testpass',
    'OLLAMA_BASE_URL': 'http://localhost:11434',
    'OLLAMA_LLM_MODEL': 'llama3.2',
    'OLLAMA_EMBED_MODEL': 'nomic-embed-text',
    'DEBUG': 'true',
    'LOG_LEVEL': 'DEBUG'
})


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'chatdb_test',
            'user': 'testuser',
            'password': 'testpass'
        },
        'ollama': {
            'base_url': 'http://localhost:11434',
            'llm_model': 'llama3.2',
            'embed_model': 'nomic-embed-text'
        },
        'app': {
            'max_result_rows': 200,
            'sql_timeout_seconds': 30,
            'top_k_retrieval': 5,
            'max_question_length': 500
        }
    }


@pytest.fixture
def mock_database_connection():
    """Mock database connection for testing."""
    mock_conn = Mock()
    mock_conn.test_connection.return_value = True
    mock_conn.execute_query.return_value = {
        'data': [{'id': 1, 'name': 'Test User'}],
        'execution_time_ms': 100,
        'success': True
    }
    mock_conn.get_schema.return_value = [
        {
            'table': 'users',
            'columns': ['id', 'name', 'email'],
            'description': 'User accounts'
        }
    ]
    return mock_conn


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing."""
    mock_client = Mock()
    
    # Mock generate method for SQL generation
    mock_client.generate.return_value = {
        'response': 'SELECT * FROM users LIMIT 200'
    }
    
    # Mock embed method for embeddings
    mock_client.embed.return_value = [0.1] * 768  # Mock embedding vector
    
    return mock_client


@pytest.fixture
def sample_schema():
    """Sample database schema for testing."""
    return [
        {
            'table': 'users',
            'columns': ['id', 'name', 'email', 'department'],
            'description': 'User accounts and information',
            'sample_data': [
                {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'department': 'Engineering'},
                {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'department': 'Product'}
            ]
        },
        {
            'table': 'tasks',
            'columns': ['id', 'title', 'status', 'assigned_to', 'project_id'],
            'description': 'Task management and assignments',
            'sample_data': [
                {'id': 1, 'title': 'Design homepage', 'status': 'completed', 'assigned_to': 1, 'project_id': 1},
                {'id': 2, 'title': 'Implement auth', 'status': 'in_progress', 'assigned_to': 2, 'project_id': 1}
            ]
        },
        {
            'table': 'projects',
            'columns': ['id', 'name', 'description', 'status'],
            'description': 'Project management',
            'sample_data': [
                {'id': 1, 'name': 'Website Redesign', 'description': 'Redesign company website', 'status': 'active'}
            ]
        }
    ]


@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return {
        'simple_select': [
            'Show all users',
            'List all tasks',
            'Display all projects',
            'Get user information'
        ],
        'aggregate_queries': [
            'Count users by department',
            'How many tasks per user?',
            'Average tasks per project',
            'Total number of completed tasks'
        ],
        'join_queries': [
            'Show users and their tasks',
            'Which projects have pending tasks?',
            'List users with overdue tasks',
            'Find task assignments by project'
        ],
        'complex_queries': [
            'Which users have more than 5 tasks?',
            'Show projects with most overdue tasks',
            'Find users with no assigned tasks',
            'List completed tasks this month'
        ],
        'dangerous_queries': [
            'Delete all users',
            'DROP TABLE tasks',
            'UPDATE users SET name = \'hacked\'',
            'SELECT * FROM pg_user'
        ]
    }


@pytest.fixture
def mock_validation_result():
    """Mock validation result for testing."""
    return {
        'is_valid': True,
        'error': None,
        'risk_level': 'LOW',
        'warnings': []
    }


@pytest.fixture
def sample_query_results():
    """Sample query results for testing."""
    return {
        'empty': [],
        'single_row': [{'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}],
        'multiple_rows': [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'},
            {'id': 3, 'name': 'Bob Johnson', 'email': 'bob@example.com'}
        ],
        'aggregated': [
            {'department': 'Engineering', 'count': 5},
            {'department': 'Product', 'count': 3},
            {'department': 'Design', 'count': 2}
        ]
    }


@pytest.fixture
def mock_pipeline_response():
    """Mock pipeline response for testing."""
    return {
        'answer': 'There are 3 users in the database.',
        'sql': 'SELECT * FROM users LIMIT 200',
        'explanation': 'This query retrieves all users from the database.',
        'results': [
            {'id': 1, 'name': 'John Doe'},
            {'id': 2, 'name': 'Jane Smith'},
            {'id': 3, 'name': 'Bob Johnson'}
        ],
        'warnings': [],
        'error': None,
        'metadata': {
            'result_count': 3,
            'schema_retrieved': True,
            'sql_validated': True,
            'execution_time_ms': 150,
            'total_time_ms': 200
        }
    }


# Mock decorators and patches
@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """Automatically mock external services for all tests."""
    
    # Mock database connection
    mock_db = Mock()
    mock_db.test_connection.return_value = True
    monkeypatch.setattr('db.connection.DatabaseConnection', Mock(return_value=mock_db))
    
    # Mock Ollama client
    mock_ollama = Mock()
    mock_ollama.generate.return_value = {'response': 'SELECT * FROM users LIMIT 200'}
    mock_ollama.embed.return_value = [0.1] * 768
    monkeypatch.setattr('rag.embedder.OllamaEmbedder', Mock(return_value=mock_ollama))
    
    # Mock vector store
    mock_vector_store = Mock()
    mock_vector_store.search.return_value = ([0.1, 0.2], [0, 1])
    mock_vector_store.get_document.return_value = {
        'table': 'users',
        'columns': ['id', 'name', 'email']
    }
    monkeypatch.setattr('rag.vector_store.FAISSVectorStore', Mock(return_value=mock_vector_store))


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: Mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: Mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: Mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "security: Mark test as security-focused"
    )
    config.addinivalue_line(
        "markers", "performance: Mark test as performance test"
    )


# Custom assertions
def assert_valid_response(response):
    """Assert that a response has the expected structure."""
    required_keys = ['answer', 'sql', 'explanation', 'results', 'warnings', 'error', 'metadata']
    for key in required_keys:
        assert key in response, f"Missing required key: {key}"
    
    # Check metadata structure
    required_metadata_keys = ['result_count', 'schema_retrieved', 'sql_validated']
    for key in required_metadata_keys:
        assert key in response['metadata'], f"Missing metadata key: {key}"


def assert_sql_is_safe(sql):
    """Assert that SQL is safe (basic checks)."""
    sql_upper = sql.upper()
    
    # Should be a SELECT query
    assert sql_upper.startswith('SELECT'), "SQL must start with SELECT"
    
    # Should not contain dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER']
    for keyword in dangerous_keywords:
        assert keyword not in sql_upper, f"SQL contains dangerous keyword: {keyword}"
    
    # Should have LIMIT clause
    assert 'LIMIT' in sql_upper, "SQL should have LIMIT clause"


# Test utilities
def create_mock_embedding(dim=768):
    """Create a mock embedding vector."""
    return [0.1] * dim


def create_mock_schema_document(table_name, columns, description=""):
    """Create a mock schema document."""
    return {
        'table': table_name,
        'columns': columns,
        'description': description,
        'sample_data': []
    }


def create_mock_query_result(data, execution_time_ms=100, success=True):
    """Create a mock query result."""
    return {
        'data': data,
        'execution_time_ms': execution_time_ms,
        'success': success,
        'error': None if success else "Mock error"
    }
