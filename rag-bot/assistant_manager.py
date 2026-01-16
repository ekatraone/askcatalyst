"""
Assistant Manager for Azure OpenAI Assistants API
Manages thread creation, message handling, and RAG operations
"""
import os
import time
import logging
from openai import AzureOpenAI
from typing import Dict, Optional, List
from retry import retry_api_call

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AssistantManager:
    """Manages Azure OpenAI Assistant operations for RAG chatbot"""

    def __init__(self):
        """Initialize Azure OpenAI client and assistant"""
        self.client = None
        self.assistant = None
        self.assistant_id = os.getenv('AZURE_OPENAI_ASSISTANT_ID')

        try:
            # Initialize Azure OpenAI client
            self.client = AzureOpenAI(
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-05-01-preview'),
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
            )

            # Get or create assistant
            if self.assistant_id:
                logger.info(f"Using existing assistant: {self.assistant_id}")
                self.assistant = self.client.beta.assistants.retrieve(self.assistant_id)
            else:
                logger.info("Creating new assistant")
                self.assistant = self._create_assistant()
                logger.info(f"Created assistant with ID: {self.assistant.id}")
                logger.info(f"Set AZURE_OPENAI_ASSISTANT_ID={self.assistant.id} in your environment")

        except Exception as e:
            logger.error(f"Failed to initialize AssistantManager: {e}")
            self.client = None
            self.assistant = None

    def _create_assistant(self):
        """Create a new assistant with file search capabilities"""
        assistant = self.client.beta.assistants.create(
            name="Ask Catalyst AI Assistant",
            instructions="""You are Ask Catalyst, an intelligent AI assistant that helps users find information from a knowledge base.

Your capabilities:
- Answer questions based on the uploaded documents
- Provide accurate citations and sources
- Admit when you don't know something
- Ask clarifying questions when needed

Guidelines:
- Be concise and clear in your responses
- Always cite sources when referencing documents
- If information isn't in the knowledge base, say so
- Be helpful and professional
""",
            model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o'),
            tools=[{"type": "file_search"}]
        )
        return assistant

    def is_enabled(self) -> bool:
        """Check if assistant manager is properly configured"""
        return self.client is not None and self.assistant is not None

    @retry_api_call
    def create_thread(self) -> Optional[str]:
        """
        Create a new conversation thread

        Returns:
            Thread ID if successful, None otherwise
        """
        try:
            thread = self.client.beta.threads.create()
            logger.info(f"Created thread: {thread.id}")
            return thread.id
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            return None

    @retry_api_call
    def add_message_to_thread(self, thread_id: str, content: str) -> bool:
        """
        Add a user message to a thread

        Args:
            thread_id: The thread ID
            content: Message content

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content
            )
            logger.info(f"Added message to thread {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add message to thread: {e}")
            return False

    @retry_api_call
    def run_assistant(self, thread_id: str, timeout: int = 30) -> Dict:
        """
        Run the assistant on a thread and wait for completion

        Args:
            thread_id: The thread ID
            timeout: Maximum time to wait in seconds

        Returns:
            Dict with response, citations, and metadata
        """
        try:
            start_time = time.time()

            # Create a run
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant.id
            )

            logger.info(f"Started run {run.id} on thread {thread_id}")

            # Poll for completion
            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

                if run.status == 'completed':
                    logger.info(f"Run {run.id} completed")
                    break
                elif run.status in ['failed', 'cancelled', 'expired']:
                    logger.error(f"Run {run.id} status: {run.status}")
                    return {
                        'success': False,
                        'error': f"Run {run.status}",
                        'status': run.status
                    }

                time.sleep(1)
            else:
                logger.error(f"Run {run.id} timed out")
                return {
                    'success': False,
                    'error': "Timeout",
                    'status': 'timeout'
                }

            # Get messages
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order='desc',
                limit=1
            )

            if not messages.data:
                return {
                    'success': False,
                    'error': "No response",
                    'status': 'no_response'
                }

            # Extract response and citations
            message = messages.data[0]
            response_text = ""
            citations = []

            for content in message.content:
                if content.type == 'text':
                    response_text += content.text.value

                    # Extract citations
                    if hasattr(content.text, 'annotations'):
                        for annotation in content.text.annotations:
                            if hasattr(annotation, 'file_citation'):
                                citation = annotation.file_citation
                                citations.append({
                                    'file_id': citation.file_id,
                                    'quote': citation.quote if hasattr(citation, 'quote') else None
                                })

            processing_time = time.time() - start_time

            return {
                'success': True,
                'response': response_text,
                'citations': citations,
                'processing_time': processing_time,
                'run_id': run.id,
                'status': 'completed'
            }

        except Exception as e:
            logger.error(f"Failed to run assistant: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': 'error'
            }

    def process_user_message(self, user_id: str, message: str, thread_id: Optional[str] = None) -> Dict:
        """
        Process a user message through the assistant

        Args:
            user_id: User identifier
            message: User message
            thread_id: Existing thread ID (optional, will create new if not provided)

        Returns:
            Dict with response and metadata
        """
        try:
            # Create thread if needed
            if not thread_id:
                thread_id = self.create_thread()
                if not thread_id:
                    return {
                        'success': False,
                        'error': "Failed to create thread"
                    }

            # Add message to thread
            if not self.add_message_to_thread(thread_id, message):
                return {
                    'success': False,
                    'error': "Failed to add message"
                }

            # Run assistant
            result = self.run_assistant(thread_id)
            result['thread_id'] = thread_id
            result['user_id'] = user_id

            return result

        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_thread_messages(self, thread_id: str, limit: int = 10) -> List[Dict]:
        """
        Get messages from a thread

        Args:
            thread_id: The thread ID
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dicts
        """
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order='desc',
                limit=limit
            )

            result = []
            for message in messages.data:
                content = ""
                for c in message.content:
                    if c.type == 'text':
                        content += c.text.value

                result.append({
                    'id': message.id,
                    'role': message.role,
                    'content': content,
                    'created_at': message.created_at
                })

            return result

        except Exception as e:
            logger.error(f"Failed to get thread messages: {e}")
            return []


# Global instance
assistant_manager = AssistantManager()
