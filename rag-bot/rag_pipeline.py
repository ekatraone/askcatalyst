"""
Main RAG Pipeline
Orchestrates the entire RAG process
"""
from typing import List, Dict, Any, Optional
import logging
from .document_processor import DocumentProcessor
from .embeddings import EmbeddingGenerator
from .vector_store import create_vector_store, VectorStore
from .retriever import Retriever
from .generator import ResponseGenerator
from .config import RAGConfig

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Complete RAG pipeline from document ingestion to response generation
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize RAG pipeline

        Args:
            config: Configuration object
        """
        self.config = config or RAGConfig()

        # Initialize components
        self.doc_processor = DocumentProcessor(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )

        self.embedding_generator = EmbeddingGenerator(
            model_name=self.config.embedding_model
        )

        self.vector_store = create_vector_store(
            store_type=self.config.vector_store_type,
            dimension=self.config.vector_dimension
        )

        self.retriever = Retriever(
            vector_store=self.vector_store,
            embedding_generator=self.embedding_generator,
            top_k=self.config.top_k,
            similarity_threshold=self.config.similarity_threshold
        )

        self.generator = ResponseGenerator(
            model_name=self.config.llm_model,
            api_key=self.config.openai_api_key or self.config.anthropic_api_key
        )

        logger.info("RAG Pipeline initialized successfully")

    def ingest_documents(self, file_paths: List[str]) -> int:
        """
        Ingest documents into the pipeline

        Args:
            file_paths: List of document file paths

        Returns:
            Number of chunks processed
        """
        logger.info(f"Ingesting {len(file_paths)} documents")

        # Process documents into chunks
        chunks = self.doc_processor.process_documents(file_paths)

        if not chunks:
            logger.warning("No chunks created from documents")
            return 0

        # Generate embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_generator.generate_embeddings(texts)

        # Store in vector store
        ids = [chunk.chunk_id for chunk in chunks]
        metadata = [
            {**chunk.metadata, 'text': chunk.text}
            for chunk in chunks
        ]

        self.vector_store.add_vectors(embeddings, ids, metadata)

        logger.info(f"Successfully ingested {len(chunks)} chunks")
        return len(chunks)

    def query(self, question: str, include_sources: bool = True) -> Dict[str, Any]:
        """
        Query the RAG system

        Args:
            question: User question
            include_sources: Whether to include source documents

        Returns:
            Response with answer and sources
        """
        logger.info(f"Processing query: {question[:100]}...")

        # Retrieve relevant documents
        context_docs = self.retriever.retrieve(question)

        if not context_docs:
            return {
                'answer': "I don't have enough information to answer this question.",
                'query': question,
                'sources': []
            }

        # Generate response
        response = self.generator.generate(
            query=question,
            context_docs=context_docs,
            include_sources=include_sources
        )

        return response

    def add_document(self, file_path: str) -> bool:
        """
        Add a single document to the system

        Args:
            file_path: Path to document

        Returns:
            Success status
        """
        try:
            result = self.ingest_documents([file_path])
            return result > 0
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False

    def save_index(self, path: str):
        """Save vector index to disk"""
        if hasattr(self.vector_store, 'save'):
            self.vector_store.save(path)
            logger.info(f"Index saved to {path}")

    def load_index(self, path: str):
        """Load vector index from disk"""
        if hasattr(self.vector_store, 'load'):
            self.vector_store.load(path)
            logger.info(f"Index loaded from {path}")
