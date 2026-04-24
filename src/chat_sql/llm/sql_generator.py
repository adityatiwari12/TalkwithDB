"""
SQL generation module using Ollama.
Converts natural language questions to SQL queries using retrieved schema.
"""

import requests
import json
from typing import Dict, Any, Optional
import re

from chat_sql.config import config


class SQLGenerator:
    """Generates SQL queries from natural language using Ollama."""
    
    def __init__(self):
        """Initialize SQL generator with Ollama."""
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_LLM_MODEL
        self._test_connection()
        self._ensure_model_available()
    
    def _test_connection(self) -> None:
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise RuntimeError(f"Cannot connect to Ollama at {self.base_url}")
            print(f"Connected to Ollama at {self.base_url}")
        except Exception as e:
            raise RuntimeError(f"Error connecting to Ollama: {e}")

    def _list_available_models(self) -> list[str]:
        """Return model names currently available in local Ollama."""
        response = requests.get(f"{self.base_url}/api/tags", timeout=5)
        response.raise_for_status()
        payload = response.json()
        models = payload.get("models", [])
        return [m.get("name", "").strip() for m in models if m.get("name")]

    def _ensure_model_available(self) -> None:
        """
        Validate configured model exists locally.
        Falls back from '<name>:latest' to '<name>' when available.
        """
        try:
            available_models = self._list_available_models()
        except Exception as e:
            raise RuntimeError(f"Unable to list Ollama models: {e}")

        if self.model in available_models:
            return

        if self.model.endswith(":latest"):
            bare_model = self.model.rsplit(":", 1)[0]
            if bare_model in available_models:
                self.model = bare_model
                return

        available_list = ", ".join(available_models) if available_models else "none"
        raise RuntimeError(
            "Configured Ollama model not found. "
            f"Configured='{self.model}', available=[{available_list}]. "
            f"Update OLLAMA_LLM_MODEL or pull the model with: ollama pull {self.model}"
        )
    
    def generate_sql(self, question: str, schema_context: str) -> Dict[str, str]:
        """
        Generate SQL query from natural language question.
        
        Args:
            question: User's natural language question
            schema_context: Relevant schema information
            
        Returns:
            Dictionary with SQL query and explanation
        """
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(question, schema_context)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent SQL
                        "num_predict": 1800,  # Increased for longer, detailed explanations
                        "num_ctx": 8192,      # Increased context window
                        "top_p": 0.9,         # Better response diversity
                        "repeat_penalty": 1.1  # Reduce repetition
                    }
                },
                timeout=90  # Increased timeout for longer responses
            )
            
            if response.status_code != 200:
                if response.status_code == 404 and "model" in response.text.lower():
                    available_models = self._list_available_models()
                    available_list = ", ".join(available_models) if available_models else "none"
                    raise RuntimeError(
                        "Ollama model not found during generation. "
                        f"Configured='{self.model}', available=[{available_list}]. "
                        f"Run: ollama pull {self.model} or set OLLAMA_LLM_MODEL to an installed model."
                    )
                raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            content = result.get("response", "").strip()
            
            # Parse response to extract SQL and explanation
            sql_query, explanation = self._parse_response(content)
            
            return {
                'sql': sql_query,
                'explanation': explanation,
                'raw_response': content
            }
            
        except Exception as e:
            raise RuntimeError(f"Error generating SQL: {e}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for SQL generation."""
        return """You are a SQL expert assistant. Generate SQL queries based on the user's question and the provided database schema.

IMPORTANT RULES:
1. ONLY generate SELECT queries. Never use INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
2. Use ONLY the tables and columns provided in the schema context.
3. Do NOT hallucinate or invent table names or column names.
4. Use proper SQL syntax with appropriate JOINs when needed.
5. Limit results to 200 rows maximum using LIMIT 200.
6. Use meaningful column aliases for clarity.
7. Consider relationships between tables when writing JOINs.

Format your response as:
SQL: [your SQL query here]
Explanation: [brief explanation of what the query does]

Example:
SQL: SELECT u.name, COUNT(t.id) as task_count FROM users u LEFT JOIN tasks t ON u.id = t.assigned_to GROUP BY u.id, u.name ORDER BY task_count DESC LIMIT 200
Explanation: This query counts the number of tasks assigned to each user and orders them by task count in descending order."""
    
    def _get_user_prompt(self, question: str, schema_context: str) -> str:
        """Get user prompt with question and schema."""
        return f"""User Question: {question}

Database Schema:
{schema_context}

Generate a SQL query to answer the user's question based on the provided schema."""
    
    def _parse_response(self, content: str) -> tuple[str, str]:
        """
        Parse LLM response to extract SQL and explanation.
        
        Args:
            content: Raw response from LLM
            
        Returns:
            Tuple of (sql_query, explanation)
        """
        # Try to extract SQL and explanation using regex
        sql_match = re.search(r'SQL:\s*(.*?)(?=Explanation:|$)', content, re.DOTALL | re.IGNORECASE)
        explanation_match = re.search(r'Explanation:\s*(.*)', content, re.DOTALL | re.IGNORECASE)
        
        if sql_match:
            sql_query = sql_match.group(1).strip()
            # Remove any extra formatting
            sql_query = re.sub(r'```sql|```', '', sql_query).strip()
        else:
            # Fallback: try to find any SQL-like content
            sql_lines = [line.strip() for line in content.split('\n') if 'SELECT' in line.upper()]
            sql_query = '\n'.join(sql_lines) if sql_lines else content.strip()
        
        explanation = explanation_match.group(1).strip() if explanation_match else "Generated SQL query to answer the question."
        
        return sql_query, explanation
    
    def validate_generated_sql(self, sql_query: str) -> bool:
        """
        Basic validation of generated SQL.
        
        Args:
            sql_query: Generated SQL query
            
        Returns:
            True if SQL appears valid
        """
        # Check if it starts with SELECT
        if not sql_query.strip().upper().startswith('SELECT'):
            return False
        
        # Check for forbidden keywords
        forbidden_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE']
        sql_upper = sql_query.upper()
        
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return False
        
        # Basic SQL syntax check
        if not re.search(r'SELECT.*FROM', sql_query, re.IGNORECASE):
            return False
        
        return True


# Global SQL generator instance
sql_generator = SQLGenerator()
