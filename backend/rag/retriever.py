# backend/rag/retriever.py
"""
Knowledge retriever for RAG pipeline.
Queries the knowledge base and formats results for LLM consumption.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from backend.rag.knowledge_base import KnowledgeBase
from config.settings import RAGConfig
from config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedContext:
    """Container for retrieved knowledge"""
    query: str
    documents: List[str]
    metadatas: List[Dict]
    relevance_scores: List[float]
    
    def get_formatted_context(self, max_docs: int = 5) -> str:
        """
        Format retrieved documents as a single context string.
        
        Args:
            max_docs: Maximum number of documents to include
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, (doc, metadata) in enumerate(zip(self.documents[:max_docs], self.metadatas[:max_docs])):
            source = metadata.get('source', 'Unknown')
            context_parts.append(f"[Source {i+1}: {source}]\n{doc}")
        
        return "\n\n".join(context_parts)


class KnowledgeRetriever:
    """Retrieves relevant medical knowledge for given queries"""
    
    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        """
        Initialize retriever.
        
        Args:
            knowledge_base: KnowledgeBase instance (creates new one if not provided)
        """
        self.kb = knowledge_base or KnowledgeBase()
        logger.info(f"✅ Knowledge retriever initialized ({self.kb.get_count()} documents)")
    
    def retrieve(
        self,
        query: str,
        n_results: int = None,
        similarity_threshold: float = None
    ) -> RetrievedContext:
        """
        Retrieve relevant knowledge for a query.
        
        Args:
            query: Search query
            n_results: Number of results to retrieve
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            RetrievedContext with relevant documents
        """
        n_results = n_results or RAGConfig.TOP_K_RESULTS
        similarity_threshold = similarity_threshold or RAGConfig.SIMILARITY_THRESHOLD
        
        logger.info(f"Retrieving knowledge for: {query[:50]}...")
        
        # Query knowledge base
        results = self.kb.query(query_text=query, n_results=n_results)
        
        # Filter by similarity threshold (distances are L2, lower is better)
        # Convert to similarity scores (0-1, higher is better)
        filtered_docs = []
        filtered_metadata = []
        filtered_scores = []
        
        for doc, metadata, distance in zip(
            results['documents'],
            results['metadatas'],
            results['distances']
        ):
            # Convert L2 distance to similarity score
            # Using: similarity = 1 / (1 + distance)
            similarity = 1 / (1 + distance)
            
            if similarity >= similarity_threshold:
                filtered_docs.append(doc)
                filtered_metadata.append(metadata)
                filtered_scores.append(similarity)
        
        logger.info(f"Retrieved {len(filtered_docs)} documents above threshold {similarity_threshold}")
        
        return RetrievedContext(
            query=query,
            documents=filtered_docs,
            metadatas=filtered_metadata,
            relevance_scores=filtered_scores
        )
    
    def retrieve_for_test(self, test_name: str, is_abnormal: bool = False) -> RetrievedContext:
        """
        Retrieve knowledge specific to a lab test.
        
        Args:
            test_name: Name of the test
            is_abnormal: Whether the test result is abnormal
            
        Returns:
            RetrievedContext with relevant medical knowledge
        """
        # Build query
        if is_abnormal:
            query = f"What does abnormal {test_name} mean? What causes high or low {test_name}?"
        else:
            query = f"What does {test_name} measure? What is {test_name} used for?"
        
        return self.retrieve(query)
    
    def get_knowledge_stats(self) -> Dict:
        """Get statistics about the knowledge base"""
        return {
            'total_documents': self.kb.get_count(),
            'collection_name': self.kb.collection_name,
            'top_k': RAGConfig.TOP_K_RESULTS,
            'similarity_threshold': RAGConfig.SIMILARITY_THRESHOLD
        }


__all__ = ["KnowledgeRetriever", "RetrievedContext"]