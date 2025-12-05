# backend/rag/embeddings.py
"""
Embedding generation using sentence transformers.
Converts text into dense vector representations for semantic search.
"""

import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
from config.settings import ModelConfig
from config.logging_config import get_logger

logger = get_logger(__name__)

class EmbeddingGenerator:
    """Generates embeddings for text using sentence transformers"""
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of the sentence transformer model
            device: Device to run on ('cpu' or 'cuda')
        """
        self.model_name = model_name or ModelConfig.EMBEDDING_MODEL_NAME
        self.device = device or ModelConfig.EMBEDDING_DEVICE
        
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        logger.info(f"✅ Embedding model loaded (dimension: {self.get_dimension()})")
    
    def generate(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for one or more texts.
        
        Args:
            texts: Single text or list of texts
            batch_size: Number of texts to process at once
            
        Returns:
            Numpy array of embeddings
        """
        # Handle single string
        if isinstance(texts, str):
            texts = [texts]
        
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        
        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def generate_single(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            1D numpy array of embedding
        """
        embedding = self.model.encode(
            text,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embedding
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.model.get_sentence_embedding_dimension()
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        emb1 = self.generate_single(text1)
        emb2 = self.generate_single(text2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)


__all__ = ["EmbeddingGenerator"]