"""
Vector store module for RAG Bot
Handles vector storage and similarity search
"""
from typing import List, Tuple, Optional
import numpy as np
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract base class for vector stores"""

    @abstractmethod
    def add_vectors(self, vectors: np.ndarray, ids: List[str], metadata: Optional[List[dict]] = None):
        """Add vectors to the store"""
        pass

    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar vectors"""
        pass

    @abstractmethod
    def delete(self, ids: List[str]):
        """Delete vectors by IDs"""
        pass


class FAISSVectorStore(VectorStore):
    """
    FAISS-based vector store for local similarity search
    """

    def __init__(self, dimension: int):
        """
        Initialize FAISS vector store

        Args:
            dimension: Dimension of vectors
        """
        self.dimension = dimension
        self.index = None
        self.id_map = {}
        self.metadata_map = {}
        self._initialize_index()

    def _initialize_index(self):
        """Initialize FAISS index"""
        try:
            import faiss
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"Initialized FAISS index with dimension {self.dimension}")
        except ImportError:
            logger.error("faiss not installed. Install with: pip install faiss-cpu")
            raise

    def add_vectors(self, vectors: np.ndarray, ids: List[str], metadata: Optional[List[dict]] = None):
        """
        Add vectors to FAISS index

        Args:
            vectors: Array of vectors
            ids: List of IDs
            metadata: Optional metadata for each vector
        """
        if len(vectors) != len(ids):
            raise ValueError("Number of vectors must match number of IDs")

        # Ensure float32 for FAISS
        vectors = vectors.astype('float32')

        # Get current index size
        current_size = self.index.ntotal

        # Add vectors to index
        self.index.add(vectors)

        # Map IDs and metadata
        for i, (vec_id, meta) in enumerate(zip(ids, metadata or [{}] * len(ids))):
            idx = current_size + i
            self.id_map[idx] = vec_id
            self.metadata_map[vec_id] = meta

        logger.info(f"Added {len(vectors)} vectors to FAISS index. Total: {self.index.ntotal}")

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[str, float, dict]]:
        """
        Search for similar vectors

        Args:
            query_vector: Query vector
            top_k: Number of results to return

        Returns:
            List of (id, distance, metadata) tuples
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []

        # Ensure correct shape and type
        query_vector = query_vector.reshape(1, -1).astype('float32')

        # Search
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))

        # Map back to IDs
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx in self.id_map:
                vec_id = self.id_map[idx]
                metadata = self.metadata_map.get(vec_id, {})
                results.append((vec_id, float(dist), metadata))

        return results

    def delete(self, ids: List[str]):
        """
        Delete vectors (not efficiently supported in FAISS, requires rebuild)

        Args:
            ids: List of IDs to delete
        """
        logger.warning("FAISS doesn't support efficient deletion. Consider rebuilding index.")
        for vec_id in ids:
            if vec_id in self.metadata_map:
                del self.metadata_map[vec_id]

    def save(self, path: str):
        """Save index to disk"""
        try:
            import faiss
            faiss.write_index(self.index, path)
            logger.info(f"Saved index to {path}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise

    def load(self, path: str):
        """Load index from disk"""
        try:
            import faiss
            self.index = faiss.read_index(path)
            logger.info(f"Loaded index from {path}")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise


def create_vector_store(store_type: str = "faiss", dimension: int = 384) -> VectorStore:
    """
    Factory function to create vector store

    Args:
        store_type: Type of vector store (faiss, pinecone, chroma)
        dimension: Vector dimension

    Returns:
        VectorStore instance
    """
    if store_type.lower() == "faiss":
        return FAISSVectorStore(dimension)
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")
