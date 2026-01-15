"""
Retrieval module for RAG Bot
Handles document retrieval based on query
"""
from typing import List, Dict, Any
import logging
import numpy as np
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves relevant documents based on query
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize retriever

        Args:
            vector_store: Vector store for similarity search
            embedding_generator: Embedding generator
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        logger.info(f"Retriever initialized with top_k={top_k}, threshold={similarity_threshold}")

    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query

        Args:
            query: Search query
            top_k: Override default top_k

        Returns:
            List of retrieved documents with metadata
        """
        k = top_k or self.top_k

        # Generate query embedding
        logger.info(f"Retrieving documents for query: {query[:100]}...")
        query_embedding = self.embedding_generator.generate_embedding(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, top_k=k)

        # Filter by threshold and format
        retrieved_docs = []
        for doc_id, distance, metadata in results:
            # Convert L2 distance to similarity score (0-1)
            similarity = 1 / (1 + distance)

            if similarity >= self.similarity_threshold:
                retrieved_docs.append({
                    'id': doc_id,
                    'similarity': similarity,
                    'distance': distance,
                    'metadata': metadata,
                    'text': metadata.get('text', '')
                })

        logger.info(f"Retrieved {len(retrieved_docs)} documents above threshold")
        return retrieved_docs

    def retrieve_with_reranking(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve and rerank documents (placeholder for advanced retrieval)

        Args:
            query: Search query
            top_k: Override default top_k

        Returns:
            List of reranked documents
        """
        # Basic implementation - retrieve more, then rerank
        k = top_k or self.top_k
        initial_results = self.retrieve(query, top_k=k * 2)

        # TODO: Implement reranking logic (e.g., cross-encoder)
        # For now, just return top_k results
        return initial_results[:k]
