"""
SQL validation module for safety and security.
Validates SQL queries to ensure they are read-only and safe.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of SQL validation."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class SQLValidator:
    """Validates SQL queries for safety and security."""
    
    def __init__(self):
        """Initialize SQL validator."""
        # Forbidden SQL keywords and patterns
        self.forbidden_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE',
            'CREATE', 'REPLACE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK',
            'EXECUTE', 'CALL', 'MERGE', 'UNION', 'INTERSECT', 'EXCEPT'
        ]
        
        # Potentially dangerous patterns
        self.dangerous_patterns = [
            r';\s*(DROP|DELETE|UPDATE|INSERT)',  # Multiple statements
            r'--.*?(DROP|DELETE|UPDATE|INSERT)',  # SQL injection via comments
            r'/\*.*?(DROP|DELETE|UPDATE|INSERT).*?\*/',  # SQL injection via block comments
            r'xp_cmdshell',  # SQL Server command execution
            r'sp_executesql',  # Dynamic SQL execution
            r'exec\s*\(',  # Function execution
        ]
        
        # System tables that should not be accessed
        self.system_tables = [
            'pg_', 'information_schema', 'sys.', 'mysql.', 'sqlite_master',
            'sqlite_sequence', 'sqlite_stat'
        ]
    
    def validate_sql(self, sql_query: str) -> ValidationResult:
        """
        Validate SQL query for safety.
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        warnings = []
        
        # Basic format validation
        if not sql_query or not sql_query.strip():
            return ValidationResult(False, "SQL query is empty")
        
        # Normalize SQL for validation
        normalized_sql = self._normalize_sql(sql_query)
        
        # Check if it starts with SELECT
        if not normalized_sql.startswith('SELECT'):
            return ValidationResult(False, "Only SELECT queries are allowed")
        
        # Check for forbidden keywords
        forbidden_found = self._check_forbidden_keywords(normalized_sql)
        if forbidden_found:
            return ValidationResult(
                False, 
                f"Forbidden keyword detected: {forbidden_found}"
            )
        
        # Check for dangerous patterns
        dangerous_found = self._check_dangerous_patterns(normalized_sql)
        if dangerous_found:
            return ValidationResult(
                False,
                f"Dangerous pattern detected: {dangerous_found}"
            )
        
        # Check for system table access
        system_table_warning = self._check_system_tables(normalized_sql)
        if system_table_warning:
            warnings.append(system_table_warning)
        
        # Check for LIMIT clause (recommend but not require)
        limit_warning = self._check_limit_clause(normalized_sql)
        if limit_warning:
            warnings.append(limit_warning)
        
        # Check for potential SQL injection patterns
        injection_warning = self._check_sql_injection(normalized_sql)
        if injection_warning:
            warnings.append(injection_warning)
        
        return ValidationResult(True, None, warnings)
    
    def _normalize_sql(self, sql_query: str) -> str:
        """
        Normalize SQL query for validation.
        
        Args:
            sql_query: Raw SQL query
            
        Returns:
            Normalized SQL query
        """
        # Remove extra whitespace and normalize case
        normalized = ' '.join(sql_query.split())
        # Convert to uppercase for pattern matching
        return normalized.upper()
    
    def _check_forbidden_keywords(self, normalized_sql: str) -> Optional[str]:
        """
        Check for forbidden SQL keywords.
        
        Args:
            normalized_sql: Normalized SQL query
            
        Returns:
            First forbidden keyword found, or None
        """
        for keyword in self.forbidden_keywords:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, normalized_sql, re.IGNORECASE):
                return keyword
        
        return None
    
    def _check_dangerous_patterns(self, normalized_sql: str) -> Optional[str]:
        """
        Check for dangerous SQL patterns.
        
        Args:
            normalized_sql: Normalized SQL query
            
        Returns:
            First dangerous pattern found, or None
        """
        for pattern in self.dangerous_patterns:
            if re.search(pattern, normalized_sql, re.IGNORECASE | re.DOTALL):
                return pattern
        
        return None
    
    def _check_system_tables(self, normalized_sql: str) -> Optional[str]:
        """
        Check for access to system tables.
        
        Args:
            normalized_sql: Normalized SQL query
            
        Returns:
            Warning message if system table found, or None
        """
        for sys_table in self.system_tables:
            if sys_table.lower() in normalized_sql.lower():
                return f"Access to system table detected: {sys_table}"
        
        return None
    
    def _check_limit_clause(self, normalized_sql: str) -> Optional[str]:
        """
        Check for LIMIT clause to prevent large result sets.
        
        Args:
            normalized_sql: Normalized SQL query
            
        Returns:
            Warning message if no LIMIT found, or None
        """
        if 'LIMIT' not in normalized_sql:
            return "Consider adding LIMIT clause to restrict result size"
        
        return None
    
    def _check_sql_injection(self, normalized_sql: str) -> Optional[str]:
        """
        Check for potential SQL injection patterns.
        
        Args:
            normalized_sql: Normalized SQL query
            
        Returns:
            Warning message if injection pattern found, or None
        """
        # Check for common injection patterns
        injection_patterns = [
            r"'.*'.*'.*'",  # Multiple single quotes
            r'".*".*".*"',  # Multiple double quotes
            r'\bor\s+1\s*=\s*1\b',  # Classic injection
            r'\band\s+1\s*=\s*1\b',  # Classic injection
            r'\bunion\s+select\b',  # UNION injection
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, normalized_sql, re.IGNORECASE):
                return "Potential SQL injection pattern detected"
        
        return None
    
    def sanitize_sql(self, sql_query: str) -> str:
        """
        Sanitize SQL query by adding safety measures.
        
        Args:
            sql_query: Original SQL query
            
        Returns:
            Sanitized SQL query
        """
        # Add LIMIT clause if not present
        if 'LIMIT' not in sql_query.upper():
            sql_query += f" LIMIT {config.MAX_RESULT_ROWS}"
        
        # Remove potentially dangerous comments
        sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
        sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
        
        return sql_query.strip()


# Global SQL validator instance
sql_validator = SQLValidator()
