"""
Vector Store Manager for Azure OpenAI
Handles document uploads and vector store operations
"""
import os
import logging
import mimetypes
from typing import List, Dict, Optional
from openai import AzureOpenAI
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages Azure OpenAI Vector Store for document RAG"""

    # Supported file formats
    SUPPORTED_FORMATS = [
        '.pdf', '.txt', '.md', '.json', '.docx', '.doc',
        '.html', '.htm', '.csv', '.xlsx', '.xls'
    ]

    MAX_FILE_SIZE = 512 * 1024 * 1024  # 512 MB

    def __init__(self):
        """Initialize Azure OpenAI client and vector store"""
        self.client = None
        self.vector_store = None
        self.vector_store_id = os.getenv('AZURE_OPENAI_VECTOR_STORE_ID')

        try:
            # Initialize Azure OpenAI client
            self.client = AzureOpenAI(
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-05-01-preview'),
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
            )

            # Get or create vector store
            if self.vector_store_id:
                logger.info(f"Using existing vector store: {self.vector_store_id}")
                self.vector_store = self.client.beta.vector_stores.retrieve(self.vector_store_id)
            else:
                logger.info("Creating new vector store")
                self.vector_store = self._create_vector_store()
                logger.info(f"Created vector store with ID: {self.vector_store.id}")
                logger.info(f"Set AZURE_OPENAI_VECTOR_STORE_ID={self.vector_store.id} in your environment")

            # Load initial documents if they exist
            self._load_initial_documents()

        except Exception as e:
            logger.error(f"Failed to initialize VectorStoreManager: {e}")
            self.client = None
            self.vector_store = None

    def _create_vector_store(self):
        """Create a new vector store"""
        vector_store = self.client.beta.vector_stores.create(
            name="Ask Catalyst Knowledge Base",
            expires_after={
                "anchor": "last_active_at",
                "days": 30
            }
        )
        return vector_store

    def _load_initial_documents(self):
        """Load initial documents from documents directory"""
        docs_dir = Path(__file__).parent / 'documents'
        if not docs_dir.exists():
            logger.info("No documents directory found, skipping initial load")
            return

        document_files = []
        for file_path in docs_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                document_files.append(str(file_path))

        if document_files:
            logger.info(f"Loading {len(document_files)} initial documents")
            result = self.upload_files(document_files)
            logger.info(f"Loaded {result.get('successful', 0)} documents successfully")

    def is_enabled(self) -> bool:
        """Check if vector store manager is properly configured"""
        return self.client is not None and self.vector_store is not None

    def validate_file(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate file for upload

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            return False, "File does not exist"

        # Check file size
        if path.stat().st_size > self.MAX_FILE_SIZE:
            return False, f"File size exceeds {self.MAX_FILE_SIZE / (1024*1024)}MB limit"

        # Check file format
        file_ext = path.suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported file format. Supported: {', '.join(self.SUPPORTED_FORMATS)}"

        # Validate MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            logger.warning(f"Could not determine MIME type for {file_path}, checking extension only")

        return True, None

    def upload_file(self, file_path: str) -> Dict:
        """
        Upload a single file to the vector store

        Args:
            file_path: Path to the file

        Returns:
            Dict with upload result
        """
        try:
            # Validate file
            is_valid, error = self.validate_file(file_path)
            if not is_valid:
                return {
                    'success': False,
                    'file_path': file_path,
                    'error': error
                }

            # Upload file
            with open(file_path, 'rb') as file_stream:
                file_obj = self.client.files.create(
                    file=file_stream,
                    purpose='assistants'
                )

            logger.info(f"Uploaded file {file_path} with ID: {file_obj.id}")

            # Add to vector store
            self.client.beta.vector_stores.files.create(
                vector_store_id=self.vector_store.id,
                file_id=file_obj.id
            )

            logger.info(f"Added file {file_obj.id} to vector store")

            return {
                'success': True,
                'file_path': file_path,
                'file_id': file_obj.id,
                'filename': Path(file_path).name
            }

        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            return {
                'success': False,
                'file_path': file_path,
                'error': str(e)
            }

    def upload_files(self, file_paths: List[str]) -> Dict:
        """
        Upload multiple files to the vector store

        Args:
            file_paths: List of file paths

        Returns:
            Dict with upload results
        """
        results = []
        successful = 0
        failed = 0

        for file_path in file_paths:
            result = self.upload_file(file_path)
            results.append(result)

            if result['success']:
                successful += 1
            else:
                failed += 1

        return {
            'total': len(file_paths),
            'successful': successful,
            'failed': failed,
            'results': results
        }

    def list_files(self) -> List[Dict]:
        """
        List all files in the vector store

        Returns:
            List of file dicts
        """
        try:
            files = self.client.beta.vector_stores.files.list(
                vector_store_id=self.vector_store.id
            )

            result = []
            for file in files.data:
                result.append({
                    'id': file.id,
                    'status': file.status,
                    'created_at': file.created_at
                })

            return result

        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from the vector store

        Args:
            file_id: The file ID

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.beta.vector_stores.files.delete(
                vector_store_id=self.vector_store.id,
                file_id=file_id
            )

            logger.info(f"Deleted file {file_id} from vector store")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False

    def get_vector_store_info(self) -> Dict:
        """
        Get information about the vector store

        Returns:
            Dict with vector store information
        """
        try:
            store = self.client.beta.vector_stores.retrieve(self.vector_store.id)
            files = self.list_files()

            return {
                'id': store.id,
                'name': store.name,
                'status': store.status,
                'file_count': len(files),
                'created_at': store.created_at,
                'expires_at': store.expires_at if hasattr(store, 'expires_at') else None
            }

        except Exception as e:
            logger.error(f"Failed to get vector store info: {e}")
            return {}

    def attach_to_assistant(self, assistant_id: str) -> bool:
        """
        Attach vector store to an assistant

        Args:
            assistant_id: The assistant ID

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.beta.assistants.update(
                assistant_id=assistant_id,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store.id]
                    }
                }
            )

            logger.info(f"Attached vector store {self.vector_store.id} to assistant {assistant_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to attach vector store to assistant: {e}")
            return False


# Global instance
vector_store_manager = VectorStoreManager()
