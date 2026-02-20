"""
Vector store implementation using FAISS for similarity search.
Handles storage and retrieval of schema embeddings.
"""

import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

from ..config import config


@dataclass
class VectorStoreItem:
    """Item stored in vector store."""
    text: str
    embedding: np.ndarray
    metadata: Dict[str, Any] = None


class VectorStore:
    """FAISS-based vector store for schema embeddings."""
    
    def __init__(self, dimension: int, store_path: str = None):
        """
        Initialize vector store.
        
        Args:
            dimension: Embedding dimension
            store_path: Path to store/load the index
        """
        self.dimension = dimension
        self.store_path = store_path or config.VECTOR_STORE_PATH
        self.index = None
        self.items: List[VectorStoreItem] = []
        self._initialize_index()
    
    def _initialize_index(self) -> None:
        """Initialize FAISS index."""
        # Use IndexFlatL2 for simple L2 distance search
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Try to load existing index if path exists
        if os.path.exists(self.store_path):
            try:
                self.load()
                print(f"Loaded existing vector store from {self.store_path}")
            except Exception as e:
                print(f"Could not load existing store: {e}")
                self.index = faiss.IndexFlatL2(self.dimension)
    
    def add_items(self, items: List[VectorStoreItem]) -> None:
        """
        Add items to vector store.
        
        Args:
            items: List of VectorStoreItem objects
        """
        if not items:
            return
        
        # Extract embeddings
        embeddings = np.array([item.embedding for item in items])
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Store items
        self.items.extend(items)
    
    def add_texts(self, texts: List[str], embeddings: np.ndarray, metadata: List[Dict] = None) -> None:
        """
        Add texts with embeddings to store.
        
        Args:
            texts: List of text strings
            embeddings: numpy array of embeddings
            metadata: Optional metadata for each text
        """
        if len(texts) != len(embeddings):
            raise ValueError("Texts and embeddings must have same length")
        
        items = []
        for i, text in enumerate(texts):
            item = VectorStoreItem(
                text=text,
                embedding=embeddings[i],
                metadata=metadata[i] if metadata else {}
            )
            items.append(item)
        
        self.add_items(items)
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[VectorStoreItem, float]]:
        """
        Search for similar items.
        
        Args:
            query_embedding: Embedding of query
            top_k: Number of results to return
            
        Returns:
            List of (item, score) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        # Reshape query for FAISS
        query_embedding = query_embedding.reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.items):
                item = self.items[idx]
                score = float(dist)  # Convert to Python float
                results.append((item, score))
        
        return results
    
    def save(self) -> None:
        """Save vector store to disk."""
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        
        # Save FAISS index
        index_path = f"{self.store_path}.faiss"
        faiss.write_index(self.index, index_path)
        
        # Save items and metadata
        data_path = f"{self.store_path}.pkl"
        with open(data_path, 'wb') as f:
            pickle.dump(self.items, f)
    
    def load(self) -> None:
        """Load vector store from disk."""
        # Load FAISS index
        index_path = f"{self.store_path}.faiss"
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
        
        # Load items and metadata
        data_path = f"{self.store_path}.pkl"
        if os.path.exists(data_path):
            with open(data_path, 'rb') as f:
                self.items = pickle.load(f)
    
    def clear(self) -> None:
        """Clear all items from store."""
        self.index.reset()
        self.items.clear()
    
    def size(self) -> int:
        """Get number of items in store."""
        return len(self.items)
