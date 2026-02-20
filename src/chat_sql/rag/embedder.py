"""
Text embedding module using Ollama.
Handles embedding of schema documents and user queries.
"""

import requests
import numpy as np
from typing import List
import json
import time

from chat_sql.config import config


class Embedder:
    """Handles text embedding using Ollama."""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedder with specified model.
        
        Args:
            model_name: Name of the Ollama embedding model
        """
        self.model_name = model_name or config.OLLAMA_EMBED_MODEL
        self.base_url = config.OLLAMA_BASE_URL
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
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of texts into vectors.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        embeddings = []
        
        # Process texts in batches to avoid overwhelming Ollama
        batch_size = 5  # Reduced batch size
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            for text in batch_texts:
                try:
                    embedding = self._embed_single_text(text)
                    embeddings.append(embedding)
                    # Reduced delay
                    time.sleep(0.05)
                except Exception as e:
                    print(f"Error embedding text: {e}")
                    # Use zero vector as fallback
                    embeddings.append(np.zeros(self.get_embedding_dimension()))
        
        return np.array(embeddings)
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query text.
        
        Args:
            query: Query text to embed
            
        Returns:
            numpy array of embedding
        """
        try:
            return self._embed_single_text(query)
        except Exception as e:
            raise RuntimeError(f"Error embedding query: {e}")
    
    def _embed_single_text(self, text: str) -> np.ndarray:
        """
        Embed a single text using Ollama API.
        
        Args:
            text: Text to embed
            
        Returns:
            numpy array of embedding
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            embedding = result.get("embedding", [])
            
            if not embedding:
                raise RuntimeError("No embedding returned from Ollama")
            
            return np.array(embedding)
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request to Ollama failed: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Ollama response: {e}")
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings.
        
        Returns:
            Embedding dimension
        """
        try:
            # Get dimension by embedding a sample text
            sample_embedding = self.embed_query("sample")
            return len(sample_embedding)
        except Exception as e:
            print(f"Error getting embedding dimension: {e}")
            # Default dimension for nomic-embed-text
            return 768


# Global embedder instance
embedder = Embedder()
