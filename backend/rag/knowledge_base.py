# backend/rag/knowledge_base.py
"""
ChromaDB-based knowledge base for storing and retrieving medical information.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from pathlib import Path

from backend.rag.embeddings import EmbeddingGenerator
from config.settings import Paths, RAGConfig
from config.logging_config import get_logger

logger = get_logger(__name__)


class KnowledgeBase:
    """Medical knowledge base using ChromaDB for vector storage"""
    
    def __init__(self, collection_name: str = None, persist_directory: Path = None):
        """
        Initialize knowledge base.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
        """
        self.collection_name = collection_name or RAGConfig.COLLECTION_NAME
        self.persist_directory = persist_directory or Paths.CHROMA_DB
        
        # Ensure directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding generator
        self.embedding_generator = EmbeddingGenerator()
        
        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB at {self.persist_directory}")
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                chroma_server_http_port=None,
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name
            )
            logger.info(f"✅ Loaded existing collection: {self.collection_name} ({self.collection.count()} items)")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Medical knowledge for report explanations"}
            )
            logger.info(f"✅ Created new collection: {self.collection_name}")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to the knowledge base.
        
        Args:
            documents: List of text documents
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document (auto-generated if not provided)
        """
        if not documents:
            logger.warning("No documents to add")
            return
        
        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} documents...")
        embeddings = self.embedding_generator.generate(documents)
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas or [{} for _ in documents],
            ids=ids
        )
        
        logger.info(f"✅ Added {len(documents)} documents to knowledge base")
    
    def query(
        self,
        query_text: str,
        n_results: int = None,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the knowledge base with semantic search.
        
        Args:
            query_text: Text to search for
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary with 'documents', 'metadatas', and 'distances'
        """
        n_results = n_results or RAGConfig.TOP_K_RESULTS
        
        # Generate embedding for query
        query_embedding = self.embedding_generator.generate_single(query_text)
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where
        )
        
        # Format results
        formatted_results = {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }
        
        logger.debug(f"Query returned {len(formatted_results['documents'])} results")
        
        return formatted_results
    
    def get_count(self) -> int:
        """Get the number of documents in the knowledge base"""
        return self.collection.count()
    
    def reset(self) -> None:
        """Delete all documents from the knowledge base"""
        logger.warning("Resetting knowledge base...")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Medical knowledge for report explanations"}
        )
        logger.info("✅ Knowledge base reset")
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete specific documents by ID"""
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents")


__all__ = ["KnowledgeBase"]