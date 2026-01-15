"""
Configuration settings for RAG Bot
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class RAGConfig:
    """Configuration for RAG Bot"""

    # Model settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "gpt-3.5-turbo"

    # Chunk settings
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Retrieval settings
    top_k: int = 5
    similarity_threshold: float = 0.7

    # Vector store settings
    vector_store_type: str = "faiss"  # Options: faiss, pinecone, chroma
    vector_dimension: int = 384

    # Database settings
    mongodb_uri: Optional[str] = os.getenv("MONGODB_URI")
    mongodb_db_name: str = "askcatalyst"
    mongodb_collection: str = "documents"

    # API Keys
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Performance settings
    batch_size: int = 32
    max_retries: int = 3
    timeout: int = 30


# Default configuration instance
config = RAGConfig()
