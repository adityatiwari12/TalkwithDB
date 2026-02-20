"""
Optimized Vector Store with persistent storage and table-level indexing.
Supports incremental updates and efficient retrieval.
"""

import faiss
import numpy as np
import pickle
import os
import json
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from chat_sql.config import config


@dataclass
class TableVectorItem:
    """Vector item for a table schema."""
    table_name: str
    text: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    checksum: str


class OptimizedVectorStore:
    """
    Optimized vector store for large-scale schema management.
    
    Features:
    - Persistent disk storage
    - Table-level indexing
    - Incremental updates
    - Efficient retrieval
    """
    
    def __init__(self, dimension: int, store_path: str = None):
        """
        Initialize optimized vector store.
        
        Args:
            dimension: Embedding dimension
            store_path: Path to store vector index
        """
        self.dimension = dimension
        self.store_path = store_path or config.VECTOR_STORE_PATH
        self.index = None
        self.table_items: Dict[str, TableVectorItem] = {}
        self.metadata_file = f"{self.store_path}_metadata.json"
        self._initialize_store()
    
    def _initialize_store(self) -> None:
        """Initialize or load existing vector store."""
        # Use IndexFlatL2 for simple L2 distance search
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Try to load existing index if path exists
        if os.path.exists(f"{self.store_path}.faiss"):
            try:
                self.load()
                print(f"Loaded existing vector store with {len(self.table_items)} tables")
            except Exception as e:
                print(f"Could not load existing store: {e}")
                self.index = faiss.IndexFlatL2(self.dimension)
                self.table_items = {}
        else:
            print("Creating new vector store")
    
    def add_table(self, table_name: str, text: str, embedding: np.ndarray, 
                 metadata: Dict[str, Any] = None, checksum: str = None) -> None:
        """
        Add or update a table in vector store.
        
        Args:
            table_name: Name of the table
            text: Formatted table schema text
            embedding: Vector embedding of the text
            metadata: Additional metadata
            checksum: Table schema checksum
        """
        # Remove existing entry if present
        if table_name in self.table_items:
            self._remove_table(table_name)
        
        # Create new item
        item = TableVectorItem(
            table_name=table_name,
            text=text,
            embedding=embedding,
            metadata=metadata or {},
            checksum=checksum
        )
        
        # Add to index
        embedding_reshaped = embedding.reshape(1, -1)
        self.index.add(embedding_reshaped)
        
        # Store item
        self.table_items[table_name] = item
        
        print(f"Added table '{table_name}' to vector store")
    
    def add_tables_batch(self, tables_data: List[Tuple[str, str, np.ndarray, Dict, str]]) -> None:
        """
        Add multiple tables in batch.
        
        Args:
            tables_data: List of (table_name, text, embedding, metadata, checksum)
        """
        if not tables_data:
            return
        
        # Prepare embeddings array
        embeddings = np.array([data[2] for data in tables_data])
        
        # Add to index
        self.index.add(embeddings)
        
        # Store items
        for table_name, text, embedding, metadata, checksum in tables_data:
            self.table_items[table_name] = TableVectorItem(
                table_name=table_name,
                text=text,
                embedding=embedding,
                metadata=metadata or {},
                checksum=checksum
            )
        
        print(f"Added {len(tables_data)} tables to vector store")
    
    def search_tables(self, query_embedding: np.ndarray, 
                   table_names: List[str] = None, 
                   top_k: int = 3) -> List[Tuple[TableVectorItem, float]]:
        """
        Search for relevant tables.
        
        Args:
            query_embedding: Embedding of the query
            table_names: Optional list of table names to restrict search
            top_k: Number of results to return
            
        Returns:
            List of (table_item, score) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        # Filter by table names if provided
        if table_names:
            filtered_items = {}
            for name in table_names:
                if name in self.table_items:
                    filtered_items[name] = self.table_items[name]
            
            if not filtered_items:
                return []
            
            # Create temporary index with filtered items
            temp_index = faiss.IndexFlatL2(self.dimension)
            embeddings = np.array([item.embedding for item in filtered_items.values()])
            temp_index.add(embeddings)
            
            # Search in filtered index
            query_reshaped = query_embedding.reshape(1, -1)
            distances, indices = temp_index.search(query_reshaped, min(top_k, len(filtered_items)))
            
            results = []
            filtered_list = list(filtered_items.values())
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(filtered_list):
                    item = filtered_list[idx]
                    score = float(dist)
                    results.append((item, score))
            
            return results
        
        # Search in full index
        query_reshaped = query_embedding.reshape(1, -1)
        distances, indices = self.index.search(query_reshaped, min(top_k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.table_items):
                item = list(self.table_items.values())[idx]
                score = float(dist)
                results.append((item, score))
        
        return results
    
    def get_table(self, table_name: str) -> Optional[TableVectorItem]:
        """
        Get a specific table from the store.
        
        Args:
            table_name: Name of the table
            
        Returns:
            TableVectorItem or None if not found
        """
        return self.table_items.get(table_name)
    
    def remove_table(self, table_name: str) -> bool:
        """
        Remove a table from the store.
        
        Args:
            table_name: Name of the table to remove
            
        Returns:
            True if removed, False if not found
        """
        return self._remove_table(table_name)
    
    def _remove_table(self, table_name: str) -> bool:
        """Internal method to remove table."""
        if table_name not in self.table_items:
            return False
        
        # Remove from items
        del self.table_items[table_name]
        
        # Rebuild index (FAISS doesn't support removal)
        if self.table_items:
            embeddings = np.array([item.embedding for item in self.table_items.values()])
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(embeddings)
        
        print(f"Removed table '{table_name}' from vector store")
        return True
    
    def update_table(self, table_name: str, text: str, embedding: np.ndarray,
                   metadata: Dict[str, Any] = None, checksum: str = None) -> None:
        """
        Update an existing table in the store.
        
        Args:
            table_name: Name of the table
            text: Updated table schema text
            embedding: New vector embedding
            metadata: Updated metadata
            checksum: New checksum
        """
        self.add_table(table_name, text, embedding, metadata, checksum)
    
    def save(self) -> None:
        """Save vector store and metadata to disk."""
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        
        # Save FAISS index
        index_path = f"{self.store_path}.faiss"
        faiss.write_index(self.index, index_path)
        
        # Save metadata
        metadata = {
            'table_items': {
                table_name: {
                    'table_name': item.table_name,
                    'text': item.text,
                    'metadata': item.metadata,
                    'checksum': item.checksum
                }
                for table_name, item in self.table_items.items()
            },
            'dimension': self.dimension,
            'total_tables': len(self.table_items),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved vector store with {len(self.table_items)} tables")
    
    def load(self) -> None:
        """Load vector store and metadata from disk."""
        # Load FAISS index
        index_path = f"{self.store_path}.faiss"
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
        
        # Load metadata
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Reconstruct table items from metadata
            self.table_items = {}
            for table_name, table_data in metadata.get('table_items', {}).items():
                # Note: We can't reconstruct embeddings from metadata
                # They need to be re-embedded when accessed
                self.table_items[table_name] = TableVectorItem(
                    table_name=table_data['table_name'],
                    text=table_data['text'],
                    embedding=np.zeros(self.dimension),  # Placeholder
                    metadata=table_data['metadata'],
                    checksum=table_data['checksum']
                )
            
            print(f"Loaded metadata for {len(self.table_items)} tables")
            
            # If we have metadata but no FAISS index, we need to rebuild
            if self.index.ntotal == 0 and len(self.table_items) > 0:
                print("FAISS index is empty, need to rebuild embeddings")
                self._rebuild_from_metadata()
    
    def _rebuild_from_metadata(self) -> None:
        """Rebuild FAISS index from metadata."""
        print("Rebuilding FAISS index from metadata...")
        
        if not self.table_items:
            print("No table items to rebuild from")
            return
        
        # Get embeddings for all tables
        from chat_sql.rag.embedder import embedder
        embedder_instance = embedder
        
        embeddings_list = []
        table_names = []
        for table_name, item in self.table_items.items():
            # Re-embed the table text
            embedding = embedder_instance.embed_query(item.text)
            item.embedding = embedding  # Update the embedding
            embeddings_list.append(embedding)
            table_names.append(table_name)
        
        # Rebuild FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        if embeddings_list:
            embeddings_array = np.array(embeddings_list)
            self.index.add(embeddings_array)
            print(f"Rebuilt FAISS index with {len(embeddings_list)} embeddings")
        
        # Save the updated index
        self.save()
    
    def get_table_names(self) -> List[str]:
        """Get list of all table names in the store."""
        return list(self.table_items.keys())
    
    def size(self) -> int:
        """Get number of tables in the store."""
        return len(self.table_items)
    
    def clear(self) -> None:
        """Clear all tables from the store."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.table_items.clear()
        print("Cleared vector store")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            'total_tables': len(self.table_items),
            'embedding_dimension': self.dimension,
            'index_size': self.index.ntotal,
            'last_updated': datetime.now().isoformat()
        }
