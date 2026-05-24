# backend/rag/embeddings.py

"""
Embedding generation system with:
- Hugging Face API embeddings
- Local fallback embeddings
- Circuit breaker protection
- Automatic failover
- Recovery retries
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
    """
    Production-grade embedding generator.

    Features:
    - HuggingFace API embeddings
    - Local SentenceTransformer fallback
    - Circuit breaker
    - Auto recovery
    - Graceful degradation
    """

    def __init__(
        self,
        model_name: str = None,
        device: str = None
    ):

        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        # =========================================================
        # CONFIG
        # =========================================================

        self.model_name = (
            model_name
            or ModelConfig.EMBEDDING_MODEL_NAME
        )

        self.device = (
            device
            or ModelConfig.EMBEDDING_DEVICE
        )

        self.dimension = 384

        # =========================================================
        # API CONFIG
        # =========================================================

        self.api_url = (
            f"https://api-inference.huggingface.co/models/"
            f"{self.model_name}"
        )

        self.api_key = os.getenv(
            "HUGGINGFACE_API_KEY"
        )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # =========================================================
        # SESSION + RETRIES
        # =========================================================

        self.session = requests.Session()

        retry_strategy = Retry(
            total=2,
            connect=2,
            read=2,
            backoff_factor=1,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504
            ],
            allowed_methods=frozenset(["POST"])
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy
        )

        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # =========================================================
        # CIRCUIT BREAKER
        # =========================================================

        self.failure_count = 0
        self.failure_threshold = 2

        self.circuit_open = False

        self.last_failure_time = None

        # wait longer before retrying internet
        self.circuit_reset_timeout = 300

        # =========================================================
        # LOCAL FALLBACK MODEL
        # =========================================================

        logger.info(
            f"Loading LOCAL embedding model: "
            f"{self.model_name} on {self.device}"
        )

        self.local_model = SentenceTransformer(
            self.model_name,
            device=self.device
        )

        logger.info(
            "✅ Local embedding model loaded"
        )

        # =========================================================
        # MODE
        # =========================================================

        self.local_mode = False

        logger.info(
            f"✅ Embedding system initialized "
            f"(model: {self.model_name})"
        )

    # =============================================================
    # MAIN GENERATE
    # =============================================================

    def generate(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32
    ) -> np.ndarray:

        if isinstance(texts, str):
            texts = [texts]

        # =========================================================
        # LOCAL MODE
        # =========================================================

        if self.local_mode:

            if self._should_retry_api():
                logger.info(
                    "Attempting API recovery..."
                )

                self.local_mode = False
                self.circuit_open = False
                self.failure_count = 0

            else:
                return self._generate_local(
                    texts,
                    batch_size
                )

        # =========================================================
        # API MODE
        # =========================================================

        try:
            return self._generate_api(
                texts,
                batch_size
            )

        except Exception as e:

            logger.error(
                f"Embedding API Error: {e}"
            )

            self._handle_failure()

            return self._generate_local(
                texts,
                batch_size
            )

    # =============================================================
    # API EMBEDDINGS
    # =============================================================

    def _generate_api(
        self,
        texts: List[str],
        batch_size: int
    ) -> np.ndarray:

        all_embeddings = []

        for i in range(0, len(texts), batch_size):

            batch = texts[i:i + batch_size]

            response = self.session.post(
                self.api_url,
                headers=self.headers,
                json={
                    "inputs": batch,
                    "options": {
                        "wait_for_model": True
                    }
                },
                timeout=(5, 8)
            )

            response.raise_for_status()

            embeddings = response.json()

            if (
                isinstance(embeddings, dict)
                and "error" in embeddings
            ):
                raise RuntimeError(
                    embeddings["error"]
                )

            if (
                isinstance(embeddings, list)
                and len(embeddings) > 0
            ):

                if isinstance(
                    embeddings[0],
                    float
                ):
                    all_embeddings.append(
                        embeddings
                    )

                else:
                    all_embeddings.extend(
                        embeddings
                    )

            else:
                raise RuntimeError(
                    "Invalid embedding response"
                )

        self.failure_count = 0

        return np.array(all_embeddings)

    # =============================================================
    # LOCAL EMBEDDINGS
    # =============================================================

    def _generate_local(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> np.ndarray:

        try:

            logger.warning(
                "⚠️ Using LOCAL embedding model"
            )

            embeddings = self.local_model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            return embeddings

        except Exception as e:

            logger.error(
                f"Local embedding failed: {e}"
            )

            return np.array([
                np.zeros(self.dimension)
                for _ in texts
            ])

    # =============================================================
    # FAILURE HANDLER
    # =============================================================

    def _handle_failure(self):

        self.failure_count += 1

        self.last_failure_time = time.time()

        if (
            self.failure_count
            >= self.failure_threshold
        ):

            self.circuit_open = True
            self.local_mode = True

            logger.error(
                "🚨 Switching to LOCAL MODE"
            )

    # =============================================================
    # API RECOVERY CHECK
    # =============================================================

    def _should_retry_api(self) -> bool:

        if not self.last_failure_time:
            return False

        elapsed = (
            time.time()
            - self.last_failure_time
        )

        return (
            elapsed >= self.circuit_reset_timeout
        )

    # =============================================================
    # SINGLE EMBEDDING
    # =============================================================

    def generate_single(
        self,
        text: str
    ) -> np.ndarray:

        embeddings = self.generate([text])

        if len(embeddings) > 0:
            return embeddings[0]

        return np.zeros(self.dimension)

    # =============================================================
    # DIMENSION
    # =============================================================

    def get_dimension(self) -> int:
        return self.dimension

    # =============================================================
    # COSINE SIMILARITY
    # =============================================================

    def compute_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:

        emb1 = self.generate_single(text1)
        emb2 = self.generate_single(text2)

        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = (
            np.dot(emb1, emb2)
            / (norm1 * norm2)
        )

        return float(similarity)


__all__ = ["EmbeddingGenerator"]