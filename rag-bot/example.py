"""
Example usage of RAG Bot
"""
import os
import logging
from rag_pipeline import RAGPipeline
from config import RAGConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_usage():
    """Basic usage example"""
    print("\n=== Basic RAG Bot Example ===\n")

    # Initialize with default config
    config = RAGConfig()
    pipeline = RAGPipeline(config)

    # Ingest documents
    print("Ingesting documents...")
    documents = [
        'sample_doc1.txt',
        'sample_doc2.txt',
    ]

    # Note: Make sure these files exist, or use your own documents
    num_chunks = pipeline.ingest_documents(documents)
    print(f"Ingested {num_chunks} chunks")

    # Query the system
    print("\nQuerying the system...")
    questions = [
        "What is the main topic of the documents?",
        "Can you summarize the key points?",
        "What are the important details?"
    ]

    for question in questions:
        print(f"\nQuestion: {question}")
        response = pipeline.query(question)
        print(f"Answer: {response['answer']}")

        if response.get('sources'):
            print("\nSources:")
            for i, source in enumerate(response['sources'], 1):
                print(f"  {i}. ID: {source['id']} (Similarity: {source['similarity']:.2f})")
                print(f"     Preview: {source['text_preview'][:100]}...")


def example_custom_config():
    """Example with custom configuration"""
    print("\n=== Custom Configuration Example ===\n")

    # Custom configuration
    config = RAGConfig(
        embedding_model="sentence-transformers/all-mpnet-base-v2",
        llm_model="gpt-4",
        chunk_size=300,
        chunk_overlap=30,
        top_k=3,
        similarity_threshold=0.8
    )

    pipeline = RAGPipeline(config)

    print("Configuration:")
    print(f"  Embedding Model: {config.embedding_model}")
    print(f"  LLM Model: {config.llm_model}")
    print(f"  Chunk Size: {config.chunk_size}")
    print(f"  Top K: {config.top_k}")


def example_save_load_index():
    """Example of saving and loading index"""
    print("\n=== Save/Load Index Example ===\n")

    config = RAGConfig()
    pipeline = RAGPipeline(config)

    # Ingest documents
    documents = ['sample_doc1.txt']
    pipeline.ingest_documents(documents)

    # Save index
    index_path = 'my_index.faiss'
    print(f"Saving index to {index_path}...")
    pipeline.save_index(index_path)

    # Create new pipeline and load index
    print("Loading index in new pipeline...")
    new_pipeline = RAGPipeline(config)
    new_pipeline.load_index(index_path)

    # Query the loaded index
    response = new_pipeline.query("Test question")
    print(f"Query successful: {bool(response)}")


def example_add_single_document():
    """Example of adding documents incrementally"""
    print("\n=== Incremental Document Addition Example ===\n")

    config = RAGConfig()
    pipeline = RAGPipeline(config)

    # Add documents one by one
    documents = ['doc1.txt', 'doc2.txt', 'doc3.txt']

    for doc in documents:
        print(f"Adding {doc}...")
        success = pipeline.add_document(doc)
        if success:
            print(f"  ✓ {doc} added successfully")
        else:
            print(f"  ✗ Failed to add {doc}")


def create_sample_documents():
    """Create sample documents for testing"""
    print("\n=== Creating Sample Documents ===\n")

    sample_texts = {
        'sample_doc1.txt': """
Artificial Intelligence (AI) is transforming the world. Machine learning, a subset of AI,
enables computers to learn from data without explicit programming. Deep learning, using neural
networks, has achieved remarkable results in image recognition, natural language processing,
and game playing. AI applications range from virtual assistants to autonomous vehicles.
        """,
        'sample_doc2.txt': """
Retrieval-Augmented Generation (RAG) is an AI framework that combines the benefits of
retrieval-based and generation-based models. RAG first retrieves relevant documents from a
knowledge base, then uses them as context for generating responses. This approach helps
reduce hallucinations and provides more accurate, grounded answers.
        """,
        'sample_doc3.txt': """
Vector databases are specialized storage systems optimized for similarity search. They store
high-dimensional vectors (embeddings) and enable efficient nearest-neighbor search. Popular
vector databases include FAISS, Pinecone, Weaviate, and Chroma. These are essential
components in RAG systems for storing and retrieving document embeddings.
        """
    }

    for filename, content in sample_texts.items():
        with open(filename, 'w') as f:
            f.write(content.strip())
        print(f"Created {filename}")


if __name__ == "__main__":
    # Uncomment the example you want to run

    # Create sample documents first
    create_sample_documents()

    # Run basic example
    # example_basic_usage()

    # Run custom config example
    # example_custom_config()

    # Run save/load example
    # example_save_load_index()

    # Run incremental addition example
    # example_add_single_document()

    print("\n=== Examples Complete ===\n")
