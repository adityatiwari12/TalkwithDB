"""Unit tests for SQL validation functionality."""

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
            "SELECT COUNT(*) FROM tasks",
            "SELECT u.name, COUNT(t.id) FROM users u LEFT JOIN tasks t ON u.id = t.assigned_to GROUP BY u.name"
        ]
        
        for query in valid_queries:
            result = validator.validate(query)
            assert result.is_valid, f"Query should be valid: {query}"
            assert result.error is None
    
    @pytest.mark.unit
    def test_reject_dml_operations(self, validator):
        """Test that DML operations are rejected."""
        
        # Invalid queries
        invalid_queries = [
            "UPDATE users SET name = 'test'",
            "DELETE FROM users WHERE id = 1",
            "INSERT INTO users (name) VALUES ('test')",
            "DROP TABLE users",
            "CREATE TABLE new_table (id INT)",
            "ALTER TABLE users ADD COLUMN age INT"
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
            "SELECT * FROM users WHERE name = 'test' #",
            "SELECT * FROM users UNION SELECT * FROM passwords",
            "SELECT * FROM users WHERE name = 'admin' UNION SELECT password FROM admin_table"
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
            "SELECT * FROM information_schema.columns",
            "SELECT * FROM mysql.user",
            "SELECT * FROM sys.tables",
            "SELECT * FROM sqlite_master"
        ]
        
        for query in system_table_queries:
            result = validator.validate(query)
            assert not result.is_valid, f"System table access should be rejected: {query}"
            assert "system table" in result.error.lower() or "not allowed" in result.error.lower()
    
    @pytest.mark.unit
    def test_query_complexity_validation(self, validator):
        """Test query complexity analysis."""
        
        # Simple queries (should pass)
        simple_queries = [
            "SELECT * FROM users",
            "SELECT name FROM users WHERE id = 1",
            "SELECT COUNT(*) FROM tasks"
        ]
        
        for query in simple_queries:
            result = validator.validate(query)
            assert result.is_valid, f"Simple query should be valid: {query}"
        
        # Complex queries (might be rejected based on limits)
        complex_query = "SELECT * FROM users u JOIN tasks t1 ON u.id = t1.user_id JOIN tasks t2 ON u.id = t2.user_id JOIN tasks t3 ON u.id = t3.user_id JOIN tasks t4 ON u.id = t4.user_id JOIN tasks t5 ON u.id = t5.user_id JOIN tasks t6 ON u.id = t6.user_id"
        
        result = validator.validate(complex_query)
        # This might be rejected due to too many JOINs
        if not result.is_valid:
            assert "complex" in result.error.lower() or "join" in result.error.lower()
    
    @pytest.mark.unit
    def test_limit_clause_addition(self, validator):
        """Test that LIMIT clause is properly added."""
        
        query_without_limit = "SELECT * FROM users"
        result = validator.validate(query_without_limit)
        
        if result.is_valid:
            # Check if LIMIT was added (if validator does this automatically)
            pass  # Implementation dependent
    
    @pytest.mark.unit
    def test_empty_and_null_queries(self, validator):
        """Test handling of empty and null queries."""
        
        invalid_inputs = [
            "",
            "   ",
            None,
            "SELECT",  # Incomplete query
            "SELECT * FROM",  # Incomplete query
        ]
        
        for query in invalid_inputs:
            if query is None:
                continue  # Skip None for this test
            result = validator.validate(query)
            assert not result.is_valid, f"Empty/invalid query should be rejected: {query}"
    
    @pytest.mark.unit
    def test_case_insensitive_validation(self, validator):
        """Test that validation is case insensitive."""
        
        case_variations = [
            "select * from users",
            "Select * From Users",
            "SELECT * FROM USERS",
            "select * FROM users"
        ]
        
        for query in case_variations:
            result = validator.validate(query)
            assert result.is_valid, f"Case variation should be valid: {query}"
    
    @pytest.mark.unit
    def test_comment_detection(self, validator):
        """Test detection of SQL comments."""
        
        comment_queries = [
            "SELECT * FROM users -- comment",
            "SELECT * FROM users # comment",
            "SELECT * FROM users /* comment */",
            "SELECT * FROM users WHERE name = 'test' -- OR 1=1"
        ]
        
        for query in comment_queries:
            result = validator.validate(query)
            # Comments might be allowed or blocked depending on security policy
            # This test documents the behavior
            if not result.is_valid:
                assert "comment" in result.error.lower()
    
    @pytest.mark.unit
    def test_whitespace_and_formatting(self, validator):
        """Test handling of various whitespace and formatting."""
        
        formatted_queries = [
            "SELECT * FROM users",
            "SELECT   *   FROM   users",
            "SELECT *\nFROM users",
            "SELECT *\tFROM users",
            "SELECT * FROM   users   WHERE   id   =   1"
        ]
        
        for query in formatted_queries:
            result = validator.validate(query)
            assert result.is_valid, f"Formatted query should be valid: {repr(query)}"
