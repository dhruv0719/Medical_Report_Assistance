# backend/rag/embeddings.py
"""
Embedding generation using Hugging Face Inference API.
Converts text into dense vector representations for semantic search.
"""

import os
import time
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
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["POST"])
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)

        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.failure_count = 0
        self.failure_threshold = 2
        self.circuit_open = False
        self.circuit_reset_timeout = 60
        self.last_failure_time = None

        self.model_name = model_name or ModelConfig.EMBEDDING_MODEL_NAME

        # Use the specific API URL for feature extraction
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")

        if not self.api_key:
            logger.error("⚠️ HUGGINGFACE_API_KEY not found. Embeddings will fail.")

        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Hardcoded for all-MiniLM-L6-v2, or could be fetched
        self.dimension = 384 
        
        logger.info(f"✅ Embedding API initialized for model: {self.model_name}")

        self.device = device or ModelConfig.EMBEDDING_DEVICE
        logger.info(f"Loading LOCAL embedding fallback model: {self.model_name} on {self.device}")

        self.local_model = SentenceTransformer(self.model_name, device=self.device)
        logger.info("✅ Local embedding fallback model loaded")
    
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
                # response = requests.post(
                #     self.api_url, 
                #     headers=self.headers, 
                #     json={"inputs": batch, "options": {"wait_for_model": True}}
                # )

                if self.circuit_open and self.last_failure_time:
                    elapsed = time.time() - self.last_failure_time

                    if elapsed < self.circuit_reset_timeout:
                        logger.warning("Circuit breaker OPEN. Skipping HF API call.")

                        fallback_embeddings = self._generate_local(batch, batch_size=batch_size
                        )

                        all_embeddings.extend(fallback_embeddings)
                        continue
                    
                    logger.info("Circuit breaker HALF-OPEN. Retrying API.")
                    self.circuit_open = False
                    self.failure_count = 0

                response = self.session.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "inputs": batch,
                        "options": {"wait_for_model":True}
                    },
                    timeout=(5,8)
                )
                response.raise_for_status()
                batch_embeddings = response.json()
                
                if isinstance(batch_embeddings, dict) and "error" in batch_embeddings:
                    raise RuntimeError(
                        f"HuggingFace API Error: {batch_embeddings['error']}"
                    )

                self.failure_count = 0

                # Verify response structure (it should be a list of lists)
                if isinstance(batch_embeddings, list) and len(batch_embeddings) > 0:
                    # Check if it's a list of floats (single embedding) or list of lists (batch)
                    if isinstance(batch_embeddings[0], float):
                         all_embeddings.append(batch_embeddings) # Single embedding returned
                    else:
                         all_embeddings.extend(batch_embeddings) # List of embeddings
                else:
                    logger.error(f"Unexpected API response format: {batch_embeddings}")
                    
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.circuit_open = True

                    logger.error(
                        f"Circuit breaker OPENED after "
                        f"{self.failure_count} failures."
                    )

                logger.error(f"Embedding API Error: {e}")
                # Return zeros as fallback to prevent crash
                # In production, you might want to retry or raise
                fallback = [np.zeros(self.dimension) for _ in batch]
                all_embeddings.extend(fallback)

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
        return self.dimension
    
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

    def _generate_local(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings using local SentenceTransformer model.
        """

        try:
            logger.warning(
                "⚠️ Using LOCAL embedding fallback model"
            )

            embeddings = self.local_model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            return embeddings   

        except Exception as e:
            logger.error(f"Local embedding failed: {e}")

            return np.array([
                np.zeros(self.dimension)
                for _ in texts
            ])


__all__ = ["EmbeddingGenerator"]