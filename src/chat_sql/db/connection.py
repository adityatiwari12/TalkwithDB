"""
Database connection management for PostgreSQL.
Handles connection lifecycle and query execution.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from chat_sql.config import config


class DatabaseConnection:
    """Manages PostgreSQL database connections and query execution."""
    
    def __init__(self):
        """Initialize database connection manager."""
        self.connection_params = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'database': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            conn.autocommit = False
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query to execute
            params: Query parameters for parameterized queries
            
        Returns:
            List of dictionaries representing rows
            
        Raises:
            ValueError: If query is not a SELECT statement
            psycopg2.Error: If query execution fails
        """
        # Basic safety check
        if not query.strip().upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                try:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    # Convert RealDictRow to regular dict
                    return [dict(row) for row in results]
                    
                except psycopg2.Error as e:
                    conn.rollback()
                    raise e
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection is successful
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except psycopg2.Error:
            return False


# Global database connection instance
db_connection = DatabaseConnection()
