"""
Embedding generation module for RAG Bot
"""
from typing import List, Union
import logging
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings for text using various models
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding generator

        Args:
            model_name: Name of the embedding model
        """
        self.model_name = model_name
        self.model = None
        logger.info(f"EmbeddingGenerator initialized with model: {model_name}")

    def _load_model(self):
        """Lazy load the embedding model"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
                raise
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                raise

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            Embedding vector as numpy array
        """
        self._load_model()
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts
            batch_size: Batch size for processing

        Returns:
            Array of embedding vectors
        """
        self._load_model()
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=True
        )
        logger.info(f"Generated embeddings for {len(texts)} texts")
        return embeddings

    def get_dimension(self) -> int:
        """
        Get the dimension of embeddings

        Returns:
            Embedding dimension
        """
        self._load_model()
        return self.model.get_sentence_embedding_dimension()
