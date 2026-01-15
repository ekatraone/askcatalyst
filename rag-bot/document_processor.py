"""
Document processing module for RAG Bot
Handles document loading, text extraction, and chunking
"""
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a processed document"""
    content: str
    metadata: Dict[str, Any]
    doc_id: str


@dataclass
class Chunk:
    """Represents a text chunk"""
    text: str
    metadata: Dict[str, Any]
    chunk_id: str
    doc_id: str


class DocumentProcessor:
    """
    Processes documents for RAG pipeline
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize document processor

        Args:
            chunk_size: Size of each text chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"DocumentProcessor initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")

    def load_document(self, file_path: str, **metadata) -> Document:
        """
        Load a document from file

        Args:
            file_path: Path to the document
            **metadata: Additional metadata

        Returns:
            Document object
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            doc_id = metadata.get('doc_id', file_path)
            return Document(
                content=content,
                metadata={'source': file_path, **metadata},
                doc_id=doc_id
            )
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            raise

    def chunk_document(self, document: Document) -> List[Chunk]:
        """
        Split document into chunks

        Args:
            document: Document to chunk

        Returns:
            List of Chunk objects
        """
        text = document.content
        chunks = []

        start = 0
        chunk_num = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunk = Chunk(
                text=chunk_text,
                metadata={
                    **document.metadata,
                    'chunk_num': chunk_num,
                    'start_pos': start,
                    'end_pos': end
                },
                chunk_id=f"{document.doc_id}_chunk_{chunk_num}",
                doc_id=document.doc_id
            )
            chunks.append(chunk)

            start = end - self.chunk_overlap
            chunk_num += 1

        logger.info(f"Document {document.doc_id} split into {len(chunks)} chunks")
        return chunks

    def process_documents(self, file_paths: List[str]) -> List[Chunk]:
        """
        Process multiple documents

        Args:
            file_paths: List of file paths

        Returns:
            List of all chunks
        """
        all_chunks = []

        for file_path in file_paths:
            try:
                doc = self.load_document(file_path)
                chunks = self.chunk_document(doc)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        return all_chunks
