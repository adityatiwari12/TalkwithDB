"""
Optimized Chat with SQL Pipeline for large-scale schemas.
Implements efficient RAG with incremental updates and pre-filtering.
"""

from typing import Dict, Any, List
import logging
import time
import sys
import os

from chat_sql.config import config
from chat_sql.rag.optimized_retriever import optimized_schema_retriever
from chat_sql.llm.sql_generator import sql_generator
from chat_sql.llm.result_formatter import ResultFormatter
from chat_sql.safety.sql_validator import sql_validator
from chat_sql.db.connection import db_connection


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizedChatWithSQLPipeline:
    """
    Optimized pipeline for large-scale Chat with SQL system.
    
    Features:
    - Lazy initialization
    - Incremental schema updates
    - Metadata pre-filtering
    - Table-level retrieval limits
    - Performance monitoring
    """
    
    def __init__(self):
        """Initialize optimized pipeline components."""
        self.schema_retriever = optimized_schema_retriever
        self.sql_generator = sql_generator
        self.result_formatter = ResultFormatter()
        self.sql_validator = sql_validator
        self.db_connection = db_connection
        
        # Validate configuration
        config.validate()
        
        # Performance tracking
        self.query_count = 0
        self.total_response_time = 0
        
        logger.info("Optimized Chat with SQL pipeline created")
    
    def chat_with_sql(self, question: str, max_tables: int = 3) -> Dict[str, Any]:
        """
        Main pipeline method with optimizations for large schemas.
        
        Args:
            question: User's natural language question
            max_tables: Maximum number of tables to retrieve
            
        Returns:
            Dictionary with answer, SQL, and metadata
        """
        start_time = time.time()
        
        try:
            self.query_count += 1
            logger.info(f"Processing query #{self.query_count}: {question}")
            
            # Step 1: Retrieve relevant schema (with pre-filtering and limits)
            schema_start = time.time()
            schema_context = self.schema_retriever.get_schema_context(
                question, max_tables=max_tables
            )
            schema_time = time.time() - schema_start
            logger.info(f"Schema retrieval took {schema_time:.3f}s")
            
            # Step 2: Generate SQL query with limited context
            sql_start = time.time()
            sql_result = self.sql_generator.generate_sql(question, schema_context)
            sql_query = sql_result['sql']
            sql_explanation = sql_result['explanation']
            sql_time = time.time() - sql_start
            logger.info(f"SQL generation took {sql_time:.3f}s")
            
            logger.info(f"Generated SQL: {sql_query}")
            
            # Step 3: Validate SQL for safety
            validation_start = time.time()
            validation_result = self.sql_validator.validate_sql(sql_query)
            validation_time = time.time() - validation_start
            
            if not validation_result.is_valid:
                logger.error(f"SQL validation failed: {validation_result.error_message}")
                return {
                    'answer': f"Cannot execute query due to safety restrictions: {validation_result.error_message}",
                    'sql': sql_query,
                    'explanation': sql_explanation,
                    'results': [],
                    'warnings': [],
                    'error': validation_result.error_message,
                    'performance': {
                        'schema_time_ms': schema_time * 1000,
                        'sql_time_ms': sql_time * 1000,
                        'validation_time_ms': validation_time * 1000,
                        'total_time_ms': (time.time() - start_time) * 1000
                    }
                }
            
            # Sanitize SQL (add LIMIT if needed)
            sanitized_sql = self.sql_validator.sanitize_sql(sql_query)
            
            # Step 4: Execute SQL query
            exec_start = time.time()
            try:
                results = self.db_connection.execute_query(sanitized_sql)
                exec_time = time.time() - exec_start
                logger.info(f"Query executed successfully in {exec_time:.3f}s, returned {len(results)} rows")
            except Exception as e:
                exec_time = time.time() - exec_start
                logger.error(f"Query execution failed after {exec_time:.3f}s: {str(e)}")
                return {
                    'answer': self.result_formatter.format_error(question, str(e)),
                    'sql': sanitized_sql,
                    'explanation': sql_explanation,
                    'results': [],
                    'warnings': validation_result.warnings,
                    'error': str(e),
                    'performance': {
                        'schema_time_ms': schema_time * 1000,
                        'sql_time_ms': sql_time * 1000,
                        'validation_time_ms': validation_time * 1000,
                        'execution_time_ms': exec_time * 1000,
                        'total_time_ms': (time.time() - start_time) * 1000
                    }
                }
            
            # Step 5: Format results into natural language
            format_start = time.time()
            answer = self.result_formatter.format_result(question, sanitized_sql, results)
            format_time = time.time() - format_start
            
            # Calculate total time
            total_time = time.time() - start_time
            self.total_response_time += total_time
            
            # Prepare response with performance metrics
            response = {
                'answer': answer,
                'sql': sanitized_sql,
                'explanation': sql_explanation,
                'results': results,
                'warnings': validation_result.warnings,
                'error': None,
                'performance': {
                    'schema_time_ms': schema_time * 1000,
                    'sql_time_ms': sql_time * 1000,
                    'validation_time_ms': validation_time * 1000,
                    'execution_time_ms': exec_time * 1000,
                    'formatting_time_ms': format_time * 1000,
                    'total_time_ms': total_time * 1000
                },
                'metadata': {
                    'result_count': len(results),
                    'tables_retrieved': len(schema_context.split('---')[0].split('\n\n')) if schema_context else 0,
                    'query_number': self.query_count,
                    'avg_response_time_ms': (self.total_response_time / self.query_count) * 1000
                }
            }
            
            logger.info(f"Pipeline completed in {total_time:.3f}s")
            return response
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Pipeline error after {total_time:.3f}s: {str(e)}")
            return {
                'answer': f"An error occurred while processing your question: {str(e)}",
                'sql': '',
                'explanation': '',
                'results': [],
                'warnings': [],
                'error': str(e),
                'performance': {
                    'total_time_ms': total_time * 1000
                }
            }
    
    def test_retrieval_performance(self, query: str) -> Dict[str, Any]:
        """
        Test retrieval performance for a query.
        
        Args:
            query: Test query
            
        Returns:
            Performance test results
        """
        return self.schema_retriever.test_retrieval(query)
    
    def get_schema_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about schema and retriever.
        
        Returns:
            Dictionary with detailed statistics
        """
        stats = self.schema_retriever.get_stats()
        stats.update({
            'pipeline_queries': self.query_count,
            'pipeline_avg_response_time_ms': (self.total_response_time / self.query_count) * 1000 if self.query_count > 0 else 0,
            'pipeline_total_response_time_ms': self.total_response_time * 1000
        })
        return stats
    
    def test_database_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection is successful
        """
        return self.db_connection.test_connection()
    
    def refresh_schema(self) -> None:
        """Force refresh of schema information."""
        logger.info("Forcing schema refresh...")
        self.schema_retriever.refresh_schema()
        logger.info("Schema refresh completed")
    
    def get_optimization_info(self) -> Dict[str, Any]:
        """
        Get information about optimizations enabled.
        
        Returns:
            Dictionary with optimization details
        """
        return {
            'features': {
                'persistent_vector_store': True,
                'incremental_updates': True,
                'table_level_chunking': True,
                'metadata_pre_filtering': True,
                'lazy_initialization': True,
                'top_k_retrieval_limit': True
            },
            'configuration': {
                'max_tables_per_query': config.TOP_K_RETRIEVAL,
                'embedding_dimension': self.schema_retriever.embedder.get_embedding_dimension(),
                'vector_store_path': config.VECTOR_STORE_PATH
            },
            'performance': {
                'queries_processed': self.query_count,
                'avg_response_time_ms': (self.total_response_time / self.query_count) * 1000 if self.query_count > 0 else 0
            }
        }


# Global optimized pipeline instance
optimized_chat_pipeline = OptimizedChatWithSQLPipeline()

def chat_with_sql(question: str) -> str:
    """
    Simple interface function for optimized pipeline.
    
    Args:
        question: User's natural language question
        
    Returns:
        Natural language answer
    """
    result = optimized_chat_pipeline.chat_with_sql(question)
    return result['answer']
