"""
Response generation module for RAG Bot
Handles LLM-based response generation with retrieved context
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generates responses using LLM with retrieved context
    """

    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Initialize response generator

        Args:
            model_name: Name of the LLM model
            api_key: API key for the LLM provider
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None
        logger.info(f"ResponseGenerator initialized with model: {model_name}")

    def _initialize_client(self):
        """Lazy load the LLM client"""
        if self.client is None:
            try:
                if "gpt" in self.model_name.lower():
                    from openai import OpenAI
                    self.client = OpenAI(api_key=self.api_key)
                    logger.info("Initialized OpenAI client")
                elif "claude" in self.model_name.lower():
                    from anthropic import Anthropic
                    self.client = Anthropic(api_key=self.api_key)
                    logger.info("Initialized Anthropic client")
                else:
                    logger.warning(f"Unknown model type: {self.model_name}")
            except ImportError as e:
                logger.error(f"Required library not installed: {e}")
                raise

    def _build_prompt(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Build prompt with context

        Args:
            query: User query
            context_docs: Retrieved context documents

        Returns:
            Formatted prompt
        """
        context_text = "\n\n".join([
            f"[Document {i+1}] (Relevance: {doc['similarity']:.2f})\n{doc['text']}"
            for i, doc in enumerate(context_docs)
        ])

        prompt = f"""You are a helpful assistant. Answer the user's question based on the provided context.

Context:
{context_text}

Question: {query}

Answer: Provide a clear, accurate answer based on the context above. If the context doesn't contain enough information to answer the question, say so clearly."""

        return prompt

    def generate(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response with context

        Args:
            query: User query
            context_docs: Retrieved context documents
            include_sources: Whether to include source information

        Returns:
            Dict with response and metadata
        """
        self._initialize_client()

        # Build prompt
        prompt = self._build_prompt(query, context_docs)

        try:
            # Generate response based on model type
            if "gpt" in self.model_name.lower():
                response = self._generate_openai(prompt)
            elif "claude" in self.model_name.lower():
                response = self._generate_anthropic(prompt)
            else:
                response = "Model not configured properly."

            result = {
                'answer': response,
                'query': query,
                'model': self.model_name
            }

            if include_sources:
                result['sources'] = [
                    {
                        'id': doc['id'],
                        'similarity': doc['similarity'],
                        'text_preview': doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text']
                    }
                    for doc in context_docs
                ]

            logger.info(f"Generated response for query: {query[:100]}...")
            return result

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def _generate_openai(self, prompt: str) -> str:
        """Generate response using OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content

    def _generate_anthropic(self, prompt: str) -> str:
        """Generate response using Anthropic API"""
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
