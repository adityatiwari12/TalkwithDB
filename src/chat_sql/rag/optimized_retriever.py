"""
Optimized Schema Retriever with metadata pre-filtering and lazy initialization.
Implements efficient retrieval for large-scale schemas.
"""

import numpy as np
import re
from typing import List, Dict, Any, Set, Optional
from datetime import datetime

from chat_sql.config import config
from chat_sql.rag.embedder import embedder
from chat_sql.rag.optimized_vector_store import OptimizedVectorStore
from chat_sql.core.schema_manager import schema_manager


class OptimizedSchemaRetriever:
    """
    Optimized schema retriever for large-scale databases.
    
    Features:
    - Metadata-based pre-filtering
    - Table-level chunking
    - Incremental updates
    - Top-K retrieval limits
    - Lazy initialization
    """
    
    def __init__(self):
        """Initialize optimized schema retriever."""
        self.embedder = embedder
        self.vector_store: Optional[OptimizedVectorStore] = None
        self.schema_manager = schema_manager
        self._initialized = False
        self._last_refresh: Optional[datetime] = None
        
        # Lazy initialization - only when needed
        self._ensure_initialized()
    
    def _ensure_initialized(self) -> None:
        """Ensure the retriever is initialized."""
        if self._initialized:
            return
        
        print("Initializing schema retriever...")
        
        # Get embedding dimension
        dimension = self.embedder.get_embedding_dimension()
        
        # Create optimized vector store
        self.vector_store = OptimizedVectorStore(dimension)
        
        # Load current schema
        self.schema_manager.get_current_schema()
        
        # Load last snapshot
        self.schema_manager.last_snapshot = self.schema_manager.load_last_snapshot()
        
        # Check for incremental updates
        self._update_schema_incremental()
        
        self._initialized = True
        self._last_refresh = datetime.now()
        
        assert self.vector_store is not None, "vector_store must be initialized"
        print(f"Schema retriever initialized with {self.vector_store.size()} tables")
    
    def _update_schema_incremental(self) -> None:
        """Update schema with only changed tables."""
        # Detect changes
        tables_to_update = self.schema_manager.get_tables_for_embedding()
        
        if not tables_to_update:
            print("No schema changes detected")
            return
        
        print(f"Updating {len(tables_to_update)} tables: {tables_to_update}")
        
        # Get documents for changed tables
        documents = []
        embeddings_list = []
        metadata_list = []
        checksums = []
        
        for table_name in tables_to_update:
            # Get table document
            doc = self.schema_manager.get_table_document(table_name)
            documents.append(doc)
            
            # Get embedding
            embedding = self.embedder.embed_query(doc)
            embeddings_list.append(embedding)
            
            # Get metadata
            metadata = {
                'table_name': table_name,
                'document_type': 'table_schema',
                'updated_at': datetime.now().isoformat()
            }
            metadata_list.append(metadata)
            
            # Get checksum
            for table in self.schema_manager.current_snapshot.tables:
                if table.name == table_name:
                    checksums.append(table.checksum)
                    break
        
        # Add to vector store
        assert self.vector_store is not None, "vector_store must be initialized"
        if len(tables_to_update) == 1:
            # Single table update
            table_name = tables_to_update[0]
            self.vector_store.add_table(
                table_name=table_name,
                text=documents[0],
                embedding=embeddings_list[0],
                metadata=metadata_list[0],
                checksum=checksums[0]
            )
        else:
            # Batch update
            tables_data = list(zip(tables_to_update, documents, embeddings_list, metadata_list, checksums))
            self.vector_store.add_tables_batch(tables_data)
        
        # Save updated vector store
        self.vector_store.save()
        
        # Save schema snapshot
        self.schema_manager.save_current_snapshot()
        
        print(f"Successfully updated {len(tables_to_update)} tables")
    
    def _extract_table_keywords(self, question: str) -> List[str]:
        """
        Extract table names from user question using keyword matching.
        
        Args:
            question: User's natural language question
            
        Returns:
            List of potential table names
        """
        # Ensure schema is loaded
        if not self.schema_manager.current_snapshot:
            self.schema_manager.get_current_schema()
        
        # Simple keyword extraction - can be enhanced with NLP
        question_lower = question.lower()
        potential_tables = []
        
        # Get all table names from current snapshot
        if self.schema_manager.current_snapshot:
            table_names = [t.name.lower() for t in self.schema_manager.current_snapshot.tables]
        else:
            table_names = []
        
        # Find exact matches
        for table_name in table_names:
            if table_name in question_lower:
                potential_tables.append(table_name)
        
        # Find partial matches (table names that appear as words)
        words = question_lower.split()
        for word in words:
            for table_name in table_names:
                if word == table_name and table_name not in potential_tables:
                    potential_tables.append(table_name)
        
        print(f"Extracted keywords: {potential_tables} from question: {question}")
        return potential_tables
    
    def _pre_filter_tables(self, question: str, max_tables: int = 10) -> List[str]:
        """
        Pre-filter tables based on metadata before vector search.
        
        Args:
            question: User's natural language question
            max_tables: Maximum tables to consider
            
        Returns:
            List of table names to search
        """
        # Extract keywords
        potential_tables = self._extract_table_keywords(question)
        
        if not potential_tables:
            # No keyword matches - will search all tables with limit
            all_tables = self.vector_store.get_table_names()
            return all_tables[:max_tables] if len(all_tables) > max_tables else all_tables
        
        # Validate that tables exist in vector store
        available_tables: List[str] = self.vector_store.get_table_names()
        filtered_tables: List[str] = []
        
        for table in potential_tables:
            # Check for exact or partial matches
            for available in available_tables:
                if table.lower() == available.lower() or table.lower() in available.lower():
                    if available not in filtered_tables:
                        filtered_tables.append(available)
                        break
        
        return filtered_tables[:max_tables] if len(filtered_tables) > max_tables else filtered_tables
    
    def retrieve_schema(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant schema information for a query.
        
        Args:
            query: User query
            top_k: Number of results to retrieve
            
        Returns:
            List of relevant schema documents with scores
        """
        self._ensure_initialized()
        
        top_k = top_k or config.TOP_K_RETRIEVAL
        
        # Pre-filter tables based on keywords
        candidate_tables = self._pre_filter_tables(query, max_tables=20)
        
        if not candidate_tables:
            print("No relevant tables found")
            return []
        
        # Embed query
        query_embedding = self.embedder.embed_query(query)
        
        assert self.vector_store is not None, "vector_store must be initialized"
        # Search in filtered table space
        results = self.vector_store.search_tables(
            query_embedding=query_embedding,
            table_names=candidate_tables,
            top_k=min(top_k, len(candidate_tables))
        )
        
        # Format results
        formatted_results = []
        for item, score in results:
            formatted_results.append({
                'text': item.text,
                'score': score,
                'metadata': item.metadata,
                'table_name': item.table_name
            })
        
        print(f"Retrieved {len(formatted_results)} relevant tables for query")
        return formatted_results
    
    def get_relevant_tables(self, query: str, limit: int = 3) -> List[str]:
        """
        Get most relevant table names for a query.
        
        Args:
            query: User query
            limit: Maximum number of tables to return
            
        Returns:
            List of relevant table names
        """
        results = self.retrieve_schema(query, top_k=limit)
        
        # Extract table names from results
        table_names: List[str] = []
        for result in results:
            if result['table_name'] not in table_names:
                table_names.append(result['table_name'])
        
        return table_names[:limit]
    
    def get_schema_context(self, query: str, max_tables: int = 3) -> str:
        """
        Get combined schema context for a query with table limit.
        
        Args:
            query: User query
            max_tables: Maximum number of tables to include
            
        Returns:
            Combined schema text as context
        """
        results = self.retrieve_schema(query, top_k=max_tables)
        
        if not results:
            return "No relevant schema information found."
        
        # Combine retrieved schema documents
        context_parts = []
        for result in results:
            context_parts.append(result['text'])
        
        context = '\n\n'.join(context_parts)
        
        # Add metadata about retrieval
        context += f"\n\n--- Retrieved {len(results)} tables ---"
        context += f"\nQuery: {query}"
        
        return context
    
    def refresh_schema(self) -> None:
        """Force refresh of schema information."""
        print("Forcing schema refresh...")
        
        # Reset initialization state
        self._initialized = False
        
        # Clear existing vector store
        if self.vector_store:
            self.vector_store.clear()
        
        # Re-initialize with fresh schema
        self._ensure_initialized()
        
        print("Schema refresh completed")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retriever.
        
        Returns:
            Dictionary with retriever statistics
        """
        self._ensure_initialized()
        
        assert self.vector_store is not None, "vector_store must be initialized"
        stats = self.vector_store.get_stats()
        stats.update({
            'last_refresh': self._last_refresh.isoformat() if self._last_refresh else None,
            'schema_manager_initialized': self.schema_manager.current_snapshot is not None,
            'total_schema_tables': len(self.schema_manager.current_snapshot.tables) if self.schema_manager.current_snapshot else 0
        })
        
        return stats
    
    def test_retrieval(self, query: str) -> Dict[str, Any]:
        """
        Test retrieval performance and results.
        
        Args:
            query: Test query
            
        Returns:
            Test results with performance metrics
        """
        import time
        
        start_time = time.time()
        
        # Pre-filtering
        pre_filter_start = time.time()
        candidate_tables = self._pre_filter_tables(query)
        pre_filter_time = time.time() - pre_filter_start
        
        # Vector search
        search_start = time.time()
        results = self.retrieve_schema(query)
        search_time = time.time() - search_start
        
        total_time = time.time() - start_time
        
        return {
            'query': query,
            'candidate_tables': candidate_tables,
            'candidate_count': len(candidate_tables),
            'retrieved_tables': [r['table_name'] for r in results],
            'retrieved_count': len(results),
            'pre_filter_time_ms': pre_filter_time * 1000,
            'search_time_ms': search_time * 1000,
            'total_time_ms': total_time * 1000,
            'results': results
        }


# Global optimized schema retriever instance
optimized_schema_retriever = OptimizedSchemaRetriever()
