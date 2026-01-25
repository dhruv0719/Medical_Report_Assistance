# backend/rag/embeddings.py
"""
Embedding generation using Hugging Face Inference API.
Converts text into dense vector representations for semantic search.
"""

import os
import requests
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
from config.settings import ModelConfig
from config.logging_config import get_logger

logger = get_logger(__name__)

class EmbeddingGenerator:
    """Generates embeddings for text using Hugging Face models."""
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of the model (default from config)
            device: Ignored (handled by Hugging Face API)
        """
        self.model_name = model_name or ModelConfig.EMBEDDING_MODEL_NAME

        # Use the specific API URL for feature extraction
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")

        if not self.api_key:
            logger.error("⚠️ HUGGINGFACE_API_KEY not found. Embeddings will fail.")

        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Hardcoded for all-MiniLM-L6-v2, or could be fetched
        self.dimension = 384 
        
        logger.info(f"✅ Embedding API initialized for model: {self.model_name}")
    
    def generate(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for one or more texts via API.
        
        Args:
            texts: Single text or list of texts
            batch_size: Number of texts per API call (to avoid payload limits)
            
        Returns:
            Numpy array of embeddings
        """
        # Handle single string
        if isinstance(texts, str):
            texts = [texts]
        
        logger.debug(f"Generating embeddings for {len(texts)} texts via API")
        
        all_embeddings = []
        
        # Process in batches to respect API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = requests.post(
                    self.api_url, 
                    headers=self.headers, 
                    json={"inputs": batch, "options": {"wait_for_model": True}}
                )
                response.raise_for_status()
                batch_embeddings = response.json()
                
                # Verify response structure (it should be a list of lists)
                if isinstance(batch_embeddings, list) and len(batch_embeddings) > 0:
                     all_embeddings.extend(batch_embeddings)
                else:
                    logger.error(f"Unexpected API response format: {batch_embeddings}")
                    
            except Exception as e:
                logger.error(f"Embedding API Error: {e}")
                # In production, you might want to retry or raise
                raise

        return np.array(all_embeddings)
    
    def generate_single(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            1D numpy array of embedding
        """
        # The API returns a list of lists [ [emb] ] for a single input list
        embeddings = self.generate([text])
        if len(embeddings) > 0:
            return embeddings[0]
        return np.zeros(self.dimension) # Fail-safe
    
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
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        similarity = np.dot(emb1, emb2) / (norm1 * norm2)
        return float(similarity)


__all__ = ["EmbeddingGenerator"]