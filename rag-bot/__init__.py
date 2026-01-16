"""
Ask Catalyst RAG Bot Package
Azure OpenAI Assistants API-based RAG system
"""

__version__ = "1.0.0"

# Import working modules only
from .assistant_manager import AssistantManager, assistant_manager
from .vector_store_manager import VectorStoreManager, vector_store_manager
from .database import ChatBotDatabase, db
from .whatsapp_handler import WhatsAppHandler, whatsapp_handler

# Removed non-existent imports:
# from .document_processor import DocumentProcessor  # REMOVED
# from .embeddings import EmbeddingGenerator          # REMOVED
# from .retriever import Retriever                    # REMOVED
# from .generator import ResponseGenerator            # REMOVED

__all__ = [
    'AssistantManager',
    'assistant_manager',
    'VectorStoreManager',
    'vector_store_manager',
    'ChatBotDatabase',
    'db',
    'WhatsAppHandler',
    'whatsapp_handler',
]
