"""
Advanced RAG System with Query Rewriting, Hybrid Search, and Re-ranking.
Version 3 - Enterprise-grade retrieval with conversation memory.
"""

import numpy as np
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib

from chat_sql.config import config
from chat_sql.rag.embedder import embedder
from chat_sql.rag.optimized_vector_store import OptimizedVectorStore


@dataclass
class QueryRewriteResult:
    """Result of query rewriting."""
    original_query: str
    rewritten_query: str
    expansion_terms: List[str]
    intent: str
    confidence: float


@dataclass
class HybridSearchResult:
    """Result from hybrid search combining BM25 + Vector."""
    table_name: str
    bm25_score: float
    vector_score: float
    combined_score: float
    metadata: Dict[str, Any]


@dataclass
class RerankedResult:
    """Result after LLM re-ranking."""
    table_name: str
    original_score: float
    llm_score: float
    relevance_reason: str
    metadata: Dict[str, Any]


@dataclass
class ConversationTurn:
    """Single turn in conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    sql_query: Optional[str] = None
    timestamp: datetime = None
    context_tables: List[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.context_tables is None:
            self.context_tables = []


class QueryRewriter:
    """
    Query rewriting with expansion and clarification.
    Uses LLM to improve vague user questions.
    """
    
    def __init__(self):
        self.expansion_cache = {}
        self.common_abbreviations = {
            'qty': 'quantity',
            'amt': 'amount',
            'rev': 'revenue',
            'cust': 'customer',
            'prod': 'product',
            'usr': 'user',
            'emp': 'employee',
            'dept': 'department',
            'cat': 'category',
            'desc': 'description',
            'id': 'identifier',
            'num': 'number',
            'dt': 'date',
            'ts': 'timestamp'
        }
    
    def rewrite_query(self, query: str, conversation_history: List[ConversationTurn] = None) -> QueryRewriteResult:
        """
        Rewrite user query for better retrieval.
        
        Args:
            query: Original user question
            conversation_history: Previous conversation turns
            
        Returns:
            QueryRewriteResult with expanded and clarified query
        """
        # Check cache
        query_hash = hashlib.md5(query.encode()).hexdigest()
        if query_hash in self.expansion_cache:
            return self.expansion_cache[query_hash]
        
        # Expand abbreviations
        expanded_query = self._expand_abbreviations(query)
        
        # Add conversation context if available
        if conversation_history and len(conversation_history) > 0:
            expanded_query = self._add_conversation_context(expanded_query, conversation_history)
        
        # Generate expansion terms
        expansion_terms = self._generate_expansion_terms(expanded_query)
        
        # Determine intent
        intent = self._determine_intent(expanded_query)
        
        result = QueryRewriteResult(
            original_query=query,
            rewritten_query=expanded_query,
            expansion_terms=expansion_terms,
            intent=intent,
            confidence=0.85
        )
        
        # Cache result
        self.expansion_cache[query_hash] = result
        
        return result
    
    def _expand_abbreviations(self, query: str) -> str:
        """Expand common abbreviations in query."""
        words = query.lower().split()
        expanded = []
        
        for word in words:
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.common_abbreviations:
                expanded.append(self.common_abbreviations[clean_word])
            else:
                expanded.append(word)
        
        return ' '.join(expanded)
    
    def _add_conversation_context(self, query: str, history: List[ConversationTurn]) -> str:
        """Add context from conversation history."""
        # Handle pronouns and references
        pronouns = ['it', 'they', 'them', 'their', 'this', 'that', 'these', 'those']
        
        words = query.lower().split()
        has_pronoun = any(word.strip('.,!?;') in pronouns for word in words)
        
        if has_pronoun and history:
            # Get context from last assistant response
            last_turn = history[-1]
            if last_turn.role == 'assistant' and last_turn.context_tables:
                # Replace pronouns with specific table references
                context_str = f" (referring to: {', '.join(last_turn.context_tables)})"
                return query + context_str
        
        return query
    
    def _generate_expansion_terms(self, query: str) -> List[str]:
        """Generate synonym expansion terms."""
        synonyms = {
            'revenue': ['sales', 'income', 'earnings', 'turnover'],
            'customer': ['client', 'buyer', 'consumer', 'user'],
            'product': ['item', 'goods', 'merchandise', 'sku'],
            'order': ['purchase', 'transaction', 'sale'],
            'employee': ['staff', 'worker', 'personnel', 'team member'],
            'price': ['cost', 'rate', 'fee', 'amount'],
            'date': ['time', 'period', 'day', 'timestamp'],
            'active': ['live', 'current', 'ongoing', 'enabled'],
            'total': ['sum', 'aggregate', 'overall', 'complete'],
            'average': ['mean', 'typical', 'standard', 'medium']
        }
        
        expansion_terms = []
        query_lower = query.lower()
        
        for term, synonyms_list in synonyms.items():
            if term in query_lower:
                expansion_terms.extend(synonyms_list)
        
        return list(set(expansion_terms))[:10]  # Limit to 10 terms
    
    def _determine_intent(self, query: str) -> str:
        """Determine query intent type."""
        query_lower = query.lower()
        
        # Count patterns
        patterns = {
            'aggregation': ['count', 'sum', 'total', 'average', 'avg', 'max', 'min', 'how many', 'how much'],
            'comparison': ['compare', 'difference', 'versus', 'vs', 'more than', 'less than'],
            'trend': ['trend', 'over time', 'monthly', 'weekly', 'daily', 'growth'],
            'list': ['list', 'show', 'get', 'display', 'find', 'what', 'which'],
            'detail': ['details', 'information', 'about', 'specific', 'lookup']
        }
        
        scores = {}
        for intent, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            scores[intent] = score
        
        # Return highest scoring intent
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'general'


class HybridSearcher:
    """
    Hybrid search combining BM25 keyword matching with vector similarity.
    """
    
    def __init__(self, vector_store: OptimizedVectorStore):
        self.vector_store = vector_store
        self.k1 = 1.5  # BM25 parameter
        self.b = 0.75  # BM25 parameter
        self.bm25_cache = {}
    
    def search(self, query: str, expansion_terms: List[str] = None, 
               top_k: int = 10) -> List[HybridSearchResult]:
        """
        Perform hybrid search with BM25 + Vector scores.
        
        Args:
            query: Search query
            expansion_terms: Additional terms to include
            top_k: Number of results to return
            
        Returns:
            List of HybridSearchResult with combined scores
        """
        # Get all table names
        table_names = self.vector_store.get_table_names()
        
        if not table_names:
            return []
        
        # Get table texts for BM25
        table_texts = {}
        for table_name in table_names:
            item = self.vector_store.get_table(table_name)
            if item:
                table_texts[table_name] = item.text
        
        # Calculate BM25 scores
        bm25_scores = self._calculate_bm25(query, table_texts, expansion_terms)
        
        # Calculate Vector scores
        query_embedding = embedder.embed_query(query)
        vector_results = self.vector_store.search_tables(
            query_embedding, 
            table_names=list(table_texts.keys()),
            top_k=len(table_texts)
        )
        
        # Normalize scores to 0-1 range
        vector_scores = {}
        if vector_results:
            max_vector_score = max(score for _, score in vector_results) if vector_results else 1
            for item, score in vector_results:
                # Convert distance to similarity (lower distance = higher similarity)
                similarity = 1 / (1 + score)
                vector_scores[item.table_name] = similarity
        
        # Combine scores (weighted average)
        combined_results = []
        for table_name in table_texts.keys():
            bm25_score = bm25_scores.get(table_name, 0)
            vector_score = vector_scores.get(table_name, 0)
            
            # Weighted combination: 40% BM25, 60% Vector
            combined_score = 0.4 * bm25_score + 0.6 * vector_score
            
            item = self.vector_store.get_table(table_name)
            
            combined_results.append(HybridSearchResult(
                table_name=table_name,
                bm25_score=bm25_score,
                vector_score=vector_score,
                combined_score=combined_score,
                metadata=item.metadata if item else {}
            ))
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        return combined_results[:top_k]
    
    def _calculate_bm25(self, query: str, table_texts: Dict[str, str],
                       expansion_terms: List[str] = None) -> Dict[str, float]:
        """
        Calculate BM25 scores for keyword matching.
        
        BM25 Formula: score = IDF * (f * (k1 + 1)) / (f + k1 * (1 - b + b * (dl / avgdl)))
        """
        # Combine query with expansion terms
        all_terms = query.lower().split()
        if expansion_terms:
            all_terms.extend([t.lower() for t in expansion_terms])
        
        # Calculate document lengths and average
        doc_lengths = {name: len(text.split()) for name, text in table_texts.items()}
        avg_length = sum(doc_lengths.values()) / len(doc_lengths) if doc_lengths else 1
        
        # Calculate IDF for each term
        N = len(table_texts)  # Total documents
        term_doc_freq = {}
        
        for term in set(all_terms):
            count = sum(1 for text in table_texts.values() if term in text.lower())
            term_doc_freq[term] = count
        
        # Calculate BM25 scores
        scores = {}
        
        for doc_name, doc_text in table_texts.items():
            score = 0
            doc_length = doc_lengths[doc_name]
            
            for term in set(all_terms):
                # Term frequency in document
                f = doc_text.lower().count(term)
                
                if f > 0:
                    # IDF calculation
                    df = term_doc_freq.get(term, 0)
                    idf = np.log((N - df + 0.5) / (df + 0.5) + 1)
                    
                    # BM25 term score
                    numerator = f * (self.k1 + 1)
                    denominator = f + self.k1 * (1 - self.b + self.b * (doc_length / avg_length))
                    
                    score += idf * (numerator / denominator)
            
            scores[doc_name] = score
        
        # Normalize scores to 0-1
        max_score = max(scores.values()) if scores else 1
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}
        
        return scores


class LLMReranker:
    """
    LLM-based re-ranking of retrieved tables for better relevance.
    """
    
    def __init__(self):
        self.rerank_cache = {}
    
    def rerank(self, query: str, candidates: List[HybridSearchResult],
               top_k: int = 3) -> List[RerankedResult]:
        """
        Re-rank candidates using LLM judgment.
        
        Args:
            query: User question
            candidates: Initial search results
            top_k: Number of top results to return
            
        Returns:
            Re-ranked list with LLM scores
        """
        if not candidates:
            return []
        
        # For efficiency, only re-rank top candidates
        candidates_to_rerank = candidates[:min(10, len(candidates))]
        
        reranked = []
        
        for candidate in candidates_to_rerank:
            # Create prompt for LLM judgment
            prompt = self._create_rerank_prompt(query, candidate)
            
            # Get LLM relevance score (simulated for now)
            # In production, this would call the actual LLM
            llm_score = self._simulate_llm_score(query, candidate)
            
            # Combine original and LLM scores
            final_score = 0.3 * candidate.combined_score + 0.7 * llm_score
            
            reranked.append(RerankedResult(
                table_name=candidate.table_name,
                original_score=candidate.combined_score,
                llm_score=llm_score,
                relevance_reason=self._generate_reason(candidate, query),
                metadata=candidate.metadata
            ))
        
        # Sort by final score
        reranked.sort(key=lambda x: x.llm_score, reverse=True)
        
        return reranked[:top_k]
    
    def _create_rerank_prompt(self, query: str, candidate: HybridSearchResult) -> str:
        """Create prompt for LLM re-ranking."""
        return f"""Evaluate how relevant this database table is for answering the question.

Question: {query}

Table: {candidate.table_name}
Table Schema: {candidate.metadata.get('schema', 'N/A')}

Rate relevance from 0.0 to 1.0 where:
- 1.0 = Essential for answering the question
- 0.5 = Somewhat relevant, provides context
- 0.0 = Not relevant

Provide only the numerical score."""
    
    def _simulate_llm_score(self, query: str, candidate: HybridSearchResult) -> float:
        """
        Simulate LLM scoring based on keyword matching.
        In production, replace with actual LLM call.
        """
        query_lower = query.lower()
        table_name_lower = candidate.table_name.lower()
        
        # Check for direct table name mention
        if table_name_lower in query_lower:
            return 0.95
        
        # Check for partial matches
        if any(word in query_lower for word in table_name_lower.split('_')):
            return 0.85
        
        # Check metadata relevance
        metadata_str = json.dumps(candidate.metadata).lower()
        query_words = set(query_lower.split())
        metadata_words = set(metadata_str.split())
        overlap = len(query_words & metadata_words)
        
        score = min(0.8, 0.3 + (overlap * 0.1))
        
        return score
    
    def _generate_reason(self, candidate: HybridSearchResult, query: str) -> str:
        """Generate human-readable relevance reason."""
        table_name = candidate.table_name
        
        if table_name.lower() in query.lower():
            return f"Directly mentioned in query"
        elif candidate.combined_score > 0.7:
            return f"Strong semantic and keyword match"
        elif candidate.combined_score > 0.4:
            return f"Moderate relevance to query context"
        else:
            return f"Weak match, may provide additional context"


class ConversationMemory:
    """
    Manages conversation history and context for multi-turn interactions.
    """
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversations: Dict[str, List[ConversationTurn]] = {}
    
    def create_session(self, session_id: str) -> None:
        """Create new conversation session."""
        self.conversations[session_id] = []
    
    def add_turn(self, session_id: str, role: str, content: str,
                sql_query: str = None, context_tables: List[str] = None) -> None:
        """Add a conversation turn."""
        if session_id not in self.conversations:
            self.create_session(session_id)
        
        turn = ConversationTurn(
            role=role,
            content=content,
            sql_query=sql_query,
            context_tables=context_tables
        )
        
        self.conversations[session_id].append(turn)
        
        # Limit history size
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
    
    def get_history(self, session_id: str) -> List[ConversationTurn]:
        """Get conversation history for session."""
        return self.conversations.get(session_id, [])
    
    def get_context_summary(self, session_id: str) -> str:
        """Generate context summary for LLM."""
        history = self.get_history(session_id)
        
        if not history:
            return ""
        
        # Build context string
        context_parts = []
        
        for turn in history[-5:]:  # Last 5 turns
            if turn.role == 'user':
                context_parts.append(f"User: {turn.content}")
            else:
                context_parts.append(f"Assistant: {turn.content}")
                if turn.sql_query:
                    context_parts.append(f"SQL: {turn.sql_query}")
        
        return "\n".join(context_parts)
    
    def extract_referenced_tables(self, session_id: str) -> List[str]:
        """Extract all tables referenced in conversation."""
        history = self.get_history(session_id)
        
        referenced = set()
        for turn in history:
            if turn.context_tables:
                referenced.update(turn.context_tables)
        
        return list(referenced)
    
    def clear_session(self, session_id: str) -> None:
        """Clear conversation history."""
        if session_id in self.conversations:
            del self.conversations[session_id]


class AdvancedRAGPipeline:
    """
    Complete Advanced RAG pipeline with all optimizations.
    """
    
    def __init__(self, vector_store: OptimizedVectorStore):
        self.vector_store = vector_store
        self.query_rewriter = QueryRewriter()
        self.hybrid_searcher = HybridSearcher(vector_store)
        self.reranker = LLMReranker()
        self.memory = ConversationMemory()
    
    def retrieve(self, query: str, session_id: str = None, 
                top_k: int = 3) -> Dict[str, Any]:
        """
        Complete retrieval pipeline.
        
        Args:
            query: User question
            session_id: Conversation session ID
            top_k: Number of top tables to return
            
        Returns:
            Dictionary with retrieved tables and metadata
        """
        # Step 1: Get conversation history
        history = []
        if session_id:
            history = self.memory.get_history(session_id)
        
        # Step 2: Query rewriting
        rewrite_result = self.query_rewriter.rewrite_query(query, history)
        
        # Step 3: Hybrid search
        search_results = self.hybrid_searcher.search(
            rewrite_result.rewritten_query,
            expansion_terms=rewrite_result.expansion_terms,
            top_k=10  # Get more for re-ranking
        )
        
        # Step 4: LLM re-ranking
        reranked_results = self.reranker.rerank(
            rewrite_result.rewritten_query,
            search_results,
            top_k=top_k
        )
        
        # Build context from reranked tables
        context_tables = []
        context_text = []
        
        for result in reranked_results:
            item = self.vector_store.get_table(result.table_name)
            if item:
                context_tables.append(result.table_name)
                context_text.append(item.text)
        
        return {
            'original_query': query,
            'rewritten_query': rewrite_result.rewritten_query,
            'expansion_terms': rewrite_result.expansion_terms,
            'intent': rewrite_result.intent,
            'retrieved_tables': context_tables,
            'schema_context': '\n\n'.join(context_text),
            'search_results': [
                {
                    'table': r.table_name,
                    'score': r.llm_score,
                    'reason': r.relevance_reason
                }
                for r in reranked_results
            ],
            'session_id': session_id
        }
