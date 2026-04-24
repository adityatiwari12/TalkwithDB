"""
Result formatting module using Ollama.
Converts SQL query results into natural language responses.
"""

import requests
import json
from typing import List, Dict, Any, Optional
import re

from chat_sql.config import config


class ResultFormatter:
    """Formats SQL query results into natural language responses using Ollama."""
    
    def __init__(self):
        """Initialize result formatter with Ollama."""
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_LLM_MODEL
        self._test_connection()
    
    def _test_connection(self) -> None:
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise RuntimeError(f"Cannot connect to Ollama at {self.base_url}")
            print(f"Connected to Ollama at {self.base_url}")
        except Exception as e:
            raise RuntimeError(f"Error connecting to Ollama: {e}")
    
    def format_result(self, question: str, sql_query: str, results: List[Dict[str, Any]]) -> str:
        """
        Format SQL query results into natural language response.
        
        Args:
            question: Original user question
            sql_query: SQL query that was executed
            results: Query results from database
            
        Returns:
            Natural language response
        """
        if not results:
            return self._format_empty_result(question)
        
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(question, sql_query, results)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,  # Slightly higher for more natural language
                        "num_predict": 2400,  # Doubled for much longer, detailed answers
                        "num_ctx": 8192,      # Doubled context window for better understanding
                        "top_p": 0.9,         # Add for better response diversity
                        "repeat_penalty": 1.1  # Reduce repetition
                    }
                },
                timeout=90  # Increased timeout for longer responses
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            # Fallback to simple formatting
            return self._fallback_format(question, results)
    
    def _format_empty_result(self, question: str) -> str:
        """
        Format response for empty query results.
        
        Args:
            question: Original user question
            
        Returns:
            Natural language response for no results
        """
        return f"No data found to answer your question: '{question}'. Please check if the data exists or try a different question."
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for result formatting."""
        return """You are a helpful assistant that converts SQL query results into natural language answers.

Your task:
1. Analyze the SQL query results carefully.
2. Convert the data into a clear, human-readable response.
3. Be explanatory, not just brief.
4. Use natural language, not technical jargon.
5. If there are multiple results, summarize patterns and key takeaways.
6. If there's no data, explain that clearly and suggest what to check next.

Guidelines:
- Use everyday language
- Be specific about numbers and counts
- Group related information
- Prefer 1 short paragraph plus 1-3 concise bullet-style insights when useful
- Always answer directly based only on the data provided"""
    
    def _get_user_prompt(self, question: str, sql_query: str, results: List[Dict[str, Any]]) -> str:
        """Get user prompt with question, SQL, and results."""
        # Format results as readable text
        results_text = self._format_results_for_prompt(results)
        
        return f"""Original Question: {question}

SQL Query Executed:
{sql_query}

Query Results:
{results_text}

Please provide a natural language answer to the original question based on these results."""
    
    def _format_results_for_prompt(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results for the LLM prompt.
        
        Args:
            results: Query results
            
        Returns:
            Formatted results string
        """
        if not results:
            return "No results found."
        
        # Get column names
        columns = list(results[0].keys())
        
        # Format as table-like structure
        lines = []
        
        # Header
        header = " | ".join(columns)
        lines.append(header)
        lines.append("-" * len(header))
        
        # Data rows (limit to first 10 for prompt)
        for row in results[:10]:
            values = [str(row.get(col, '')) for col in columns]
            line = " | ".join(values)
            lines.append(line)
        
        if len(results) > 10:
            lines.append(f"... and {len(results) - 10} more rows")
        
        return "\n".join(lines)
    
    def _fallback_format(self, question: str, results: List[Dict[str, Any]]) -> str:
        """
        Fallback formatting when LLM fails.
        
        Args:
            question: Original question
            results: Query results
            
        Returns:
            Simple formatted response
        """
        if not results:
            return f"No results found for your question."
        
        # Simple formatting based on result structure
        count = len(results)
        
        if count == 1:
            # Single result - describe the row
            row = results[0]
            if len(row) == 1:
                value = list(row.values())[0]
                return f"The answer is: {value}"
            else:
                # Multiple columns - format as key-value pairs
                pairs = [f"{k}: {v}" for k, v in row.items()]
                return f"Found: {', '.join(pairs)}"
        else:
            # Multiple results - summarize count
            return f"Found {count} results matching your question."
    
    def format_error(self, question: str, error_message: str) -> str:
        """
        Format error response.
        
        Args:
            question: Original question
            error_message: Error message from SQL execution
            
        Returns:
            User-friendly error message
        """
        return f"I couldn't answer your question '{question}' due to a database error. Please try rephrasing your question or contact support if the issue persists."
