"""
Schema retriever using RAG (Retrieval-Augmented Generation).
Retrieves relevant schema information based on user queries.
"""

from typing import List, Dict, Any
import numpy as np

from config import config
from rag.embedder import embedder
from rag.vector_store import VectorStore, VectorStoreItem
from db.schema_loader import schema_loader


class SchemaRetriever:
    """Retrieves relevant schema information using RAG."""
    
    def __init__(self):
        """Initialize schema retriever."""
        self.embedder = embedder
        self.vector_store = None
        self.schema_loader = schema_loader
        self._initialize_vector_store()
    
    def _initialize_vector_store(self) -> None:
        """Initialize and populate vector store with schema information."""
        # Get embedding dimension
        dimension = self.embedder.get_embedding_dimension()
        
        # Create vector store
        self.vector_store = VectorStore(dimension)
        
        # Load and embed schema documents
        self._populate_vector_store()
    
    def _populate_vector_store(self) -> None:
        """Populate vector store with schema documents."""
        # Get schema documents
        documents = self.schema_loader.schema_to_documents()
        
        if not documents:
            print("No schema documents found")
            return
        
        # Embed documents
        print(f"Embedding {len(documents)} schema documents...")
        embeddings = self.embedder.embed_texts(documents)
        
        # Add to vector store
        self.vector_store.add_texts(documents, embeddings)
        
        # Save vector store
        self.vector_store.save()
        
        print(f"Vector store populated with {len(documents)} documents")
    
    def retrieve_schema(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant schema information for a query.
        
        Args:
            query: User query
            top_k: Number of results to retrieve
            
        Returns:
            List of relevant schema documents with scores
        """
        top_k = top_k or config.TOP_K_RETRIEVAL
        
        # Embed query
        query_embedding = self.embedder.embed_query(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k)
        
        # Format results
        formatted_results = []
        for item, score in results:
            formatted_results.append({
                'text': item.text,
                'score': score,
                'metadata': item.metadata
            })
        
        return formatted_results
    
    def get_relevant_tables(self, query: str) -> List[str]:
        """
        Extract table names from retrieved schema.
        
        Args:
            query: User query
            
        Returns:
            List of relevant table names
        """
        results = self.retrieve_schema(query)
        
        # Extract table names from results
        tables = set()
        for result in results:
            text = result['text']
            if text.startswith('Table:'):
                table_name = text.split('\n')[0].replace('Table:', '').strip()
                tables.add(table_name)
        
        return list(tables)
    
    def get_schema_context(self, query: str) -> str:
        """
        Get combined schema context for a query.
        
        Args:
            query: User query
            
        Returns:
            Combined schema text as context
        """
        results = self.retrieve_schema(query)
        
        # Combine all retrieved schema documents
        context_parts = []
        for result in results:
            context_parts.append(result['text'])
        
        return '\n\n'.join(context_parts)
    
    def refresh_schema(self) -> None:
        """Refresh schema information in vector store."""
        # Clear existing store
        self.vector_store.clear()
        
        # Repopulate with fresh schema
        self._populate_vector_store()
        
        print("Schema refreshed in vector store")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retriever.
        
        Returns:
            Dictionary with retriever statistics
        """
        return {
            'total_documents': self.vector_store.size(),
            'embedding_dimension': self.embedder.get_embedding_dimension(),
            'model_name': self.embedder.model_name
        }


# Global schema retriever instance
schema_retriever = SchemaRetriever()
