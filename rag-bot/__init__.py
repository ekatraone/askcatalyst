"""
RAG Bot - Retrieval-Augmented Generation Bot
"""

__version__ = "0.1.0"
__author__ = "Ask Catalyst Team"

from .document_processor import DocumentProcessor
from .embeddings import EmbeddingGenerator
from .retriever import Retriever
from .generator import ResponseGenerator

__all__ = [
    'DocumentProcessor',
    'EmbeddingGenerator',
    'Retriever',
    'ResponseGenerator'
]
