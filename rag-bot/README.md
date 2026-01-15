# RAG Bot - Retrieval-Augmented Generation Bot

A modular RAG (Retrieval-Augmented Generation) system for building intelligent question-answering bots.

## Features

- **Document Processing**: Load and chunk documents for efficient retrieval
- **Embeddings**: Generate semantic embeddings using sentence transformers
- **Vector Storage**: FAISS-based vector store for fast similarity search
- **Retrieval**: Intelligent document retrieval with configurable parameters
- **Generation**: LLM-based response generation with context
- **Modular Architecture**: Easy to extend and customize

## Architecture

```
┌─────────────┐
│  Documents  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Document Processor  │  ← Chunking & Parsing
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Embedding Generator │  ← Text → Vectors
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Vector Store      │  ← FAISS / Pinecone
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│     Retriever       │  ← Similarity Search
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Response Generator  │  ← LLM + Context
└─────────────────────┘
```

## Installation

```bash
# Install required dependencies
pip install sentence-transformers faiss-cpu openai anthropic numpy
```

## Quick Start

```python
from rag_bot import RAGPipeline
from rag_bot.config import RAGConfig

# Initialize pipeline
config = RAGConfig()
pipeline = RAGPipeline(config)

# Ingest documents
documents = ['doc1.txt', 'doc2.txt', 'doc3.txt']
pipeline.ingest_documents(documents)

# Query
response = pipeline.query("What is RAG?")
print(response['answer'])
print(response['sources'])
```

## Configuration

Configure the RAG system via `config.py`:

```python
config = RAGConfig(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    llm_model="gpt-3.5-turbo",
    chunk_size=500,
    chunk_overlap=50,
    top_k=5,
    similarity_threshold=0.7
)
```

## Modules

### document_processor.py
Handles document loading and chunking:
- Load documents from files
- Split into manageable chunks
- Preserve metadata

### embeddings.py
Generate semantic embeddings:
- Support for sentence-transformers models
- Batch processing
- Configurable models

### vector_store.py
Vector storage and retrieval:
- FAISS implementation
- Extensible for other stores (Pinecone, Chroma)
- Save/load indices

### retriever.py
Intelligent retrieval:
- Similarity search
- Threshold filtering
- Reranking support

### generator.py
LLM-based response generation:
- OpenAI GPT support
- Anthropic Claude support
- Context-aware prompting

### rag_pipeline.py
Complete RAG orchestration:
- End-to-end pipeline
- Document ingestion
- Query processing

## API Reference

### RAGPipeline

```python
pipeline = RAGPipeline(config)

# Ingest documents
pipeline.ingest_documents(['file1.txt', 'file2.txt'])

# Query
response = pipeline.query("Your question here")

# Save/load index
pipeline.save_index('index.faiss')
pipeline.load_index('index.faiss')
```

## Advanced Usage

### Custom Vector Store

```python
from rag_bot.vector_store import VectorStore

class CustomVectorStore(VectorStore):
    def add_vectors(self, vectors, ids, metadata):
        # Your implementation
        pass

    def search(self, query_vector, top_k):
        # Your implementation
        pass
```

### Custom Embeddings

```python
from rag_bot.embeddings import EmbeddingGenerator

generator = EmbeddingGenerator(
    model_name="custom-model-name"
)
```

## Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
MONGODB_URI=mongodb://localhost:27017
```

## Testing

```bash
# Run tests (coming soon)
pytest tests/
```

## Performance Tips

1. **Chunk Size**: Balance between context and precision (500-1000 tokens)
2. **Overlap**: Prevents information loss at boundaries (50-100 tokens)
3. **Top-K**: Retrieve enough context without noise (3-10 documents)
4. **Batch Processing**: Use batching for embedding generation

## Troubleshooting

### FAISS not found
```bash
pip install faiss-cpu
# or for GPU
pip install faiss-gpu
```

### Sentence Transformers error
```bash
pip install sentence-transformers
```

### OpenAI API errors
Check your API key and quota

## Contributing

See CONTRIBUTING.md for guidelines.

## License

See LICENSE file.

## Resources

- [RAG Paper](https://arxiv.org/abs/2005.11401)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
