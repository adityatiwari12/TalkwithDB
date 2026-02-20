"""
Main pipeline for Chat with SQL system.
Orchestrates the complete RAG-based SQL generation and execution pipeline.
"""

from typing import Dict, Any, List
import logging

from ..config import config
from ..rag.retriever import schema_retriever
from ..llm.sql_generator import sql_generator
from ..llm.result_formatter import ResultFormatter
from ..safety.sql_validator import sql_validator
from ..db.connection import db_connection


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatWithSQLPipeline:
    """Main pipeline for Chat with SQL system."""
    
    def __init__(self):
        """Initialize the pipeline components."""
        self.schema_retriever = schema_retriever
        self.sql_generator = sql_generator
        self.result_formatter = ResultFormatter()
        self.sql_validator = sql_validator
        self.db_connection = db_connection
        
        # Validate configuration
        config.validate()
        
        logger.info("Chat with SQL pipeline initialized")
    
    def chat_with_sql(self, question: str) -> Dict[str, Any]:
        """
        Main pipeline method to answer natural language questions with SQL.
        
        Args:
            question: User's natural language question
            
        Returns:
            Dictionary with answer, SQL, and metadata
        """
        try:
            logger.info(f"Processing question: {question}")
            
            # Step 1: Retrieve relevant schema information
            schema_context = self.schema_retriever.get_schema_context(question)
            logger.info("Schema retrieval completed")
            
            # Step 2: Generate SQL query
            sql_result = self.sql_generator.generate_sql(question, schema_context)
            sql_query = sql_result['sql']
            sql_explanation = sql_result['explanation']
            
            logger.info(f"Generated SQL: {sql_query}")
            
            # Step 3: Validate SQL for safety
            validation_result = self.sql_validator.validate_sql(sql_query)
            
            if not validation_result.is_valid:
                logger.error(f"SQL validation failed: {validation_result.error_message}")
                return {
                    'answer': f"Cannot execute query due to safety restrictions: {validation_result.error_message}",
                    'sql': sql_query,
                    'explanation': sql_explanation,
                    'results': [],
                    'warnings': [],
                    'error': validation_result.error_message
                }
            
            # Sanitize SQL (add LIMIT if needed)
            sanitized_sql = self.sql_validator.sanitize_sql(sql_query)
            
            # Step 4: Execute SQL query
            try:
                results = self.db_connection.execute_query(sanitized_sql)
                logger.info(f"Query executed successfully, returned {len(results)} rows")
            except Exception as e:
                logger.error(f"Query execution failed: {str(e)}")
                return {
                    'answer': self.result_formatter.format_error(question, str(e)),
                    'sql': sanitized_sql,
                    'explanation': sql_explanation,
                    'results': [],
                    'warnings': validation_result.warnings,
                    'error': str(e)
                }
            
            # Step 5: Format results into natural language
            answer = self.result_formatter.format_result(question, sanitized_sql, results)
            
            # Prepare response
            response = {
                'answer': answer,
                'sql': sanitized_sql,
                'explanation': sql_explanation,
                'results': results,
                'warnings': validation_result.warnings,
                'error': None,
                'metadata': {
                    'result_count': len(results),
                    'schema_retrieved': True,
                    'sql_validated': True
                }
            }
            
            logger.info("Pipeline completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            return {
                'answer': f"An error occurred while processing your question: {str(e)}",
                'sql': '',
                'explanation': '',
                'results': [],
                'warnings': [],
                'error': str(e)
            }
    
    def get_schema_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the schema and retriever.
        
        Returns:
            Dictionary with schema statistics
        """
        return self.schema_retriever.get_stats()
    
    def test_database_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection is successful
        """
        return self.db_connection.test_connection()
    
    def refresh_schema(self) -> None:
        """Refresh the schema information in the retriever."""
        self.schema_retriever.refresh_schema()
        logger.info("Schema refreshed")


# Global pipeline instance
chat_pipeline = ChatWithSQLPipeline()


def chat_with_sql(question: str) -> str:
    """
    Simple interface function for the pipeline.
    
    Args:
        question: User's natural language question
        
    Returns:
        Natural language answer
    """
    result = chat_pipeline.chat_with_sql(question)
    return result['answer']
