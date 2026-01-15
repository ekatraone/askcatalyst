# Ask Catalyst - RAG Bot Project

## Project Overview
Ask Catalyst is a RAG (Retrieval-Augmented Generation) bot project designed to provide intelligent question-answering capabilities using document retrieval and language model generation.

## Current Structure
```
askcatalyst/
├── CLAUDE.MD                 # This file - Project documentation for Claude
├── README.md                 # Public-facing project documentation
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # Project license
├── requirements.txt          # Python dependencies
├── main.py                   # Main application entry point
├── operations.py             # Core operations and utilities
├── mongoDB.py                # MongoDB database operations
├── WATI.py                   # WATI integration module
└── rag-bot/                  # RAG bot implementation (to be added)
```

## Development Branch
- **Active Branch**: `claude/setup-ragbot-ask-catalyst-i4WeR`
- **Main Branch**: To be determined
- All development should occur on the claude branch

## RAG Bot Architecture (Planned)

### Components
1. **Document Processing**
   - Text extraction and chunking
   - Embedding generation
   - Vector storage

2. **Retrieval System**
   - Vector similarity search
   - Context ranking and filtering
   - Hybrid search (keyword + semantic)

3. **Generation Pipeline**
   - Query understanding
   - Context augmentation
   - Response generation
   - Answer verification

4. **Data Storage**
   - MongoDB for metadata and user data
   - Vector database for embeddings (e.g., Pinecone, Weaviate, or FAISS)

### Technology Stack
- **Framework**: Python 3.x
- **Database**: MongoDB (already integrated)
- **Vector Store**: TBD (Pinecone/FAISS/Chroma)
- **LLM Integration**: TBD (OpenAI/Anthropic/Local models)
- **Embeddings**: TBD (OpenAI/Sentence Transformers)

## Setup Instructions

### Prerequisites
```bash
python >= 3.8
pip
MongoDB instance
```

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd askcatalyst

# Checkout development branch
git checkout claude/setup-ragbot-ask-catalyst-i4WeR

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file with the following variables:
```env
MONGODB_URI=<your-mongodb-connection-string>
OPENAI_API_KEY=<your-api-key>  # If using OpenAI
ANTHROPIC_API_KEY=<your-api-key>  # If using Anthropic
WATI_API_KEY=<your-wati-key>
# Add other environment variables as needed
```

## Development Workflow

### Git Workflow
1. Work on feature branch: `claude/setup-ragbot-ask-catalyst-i4WeR`
2. Make atomic commits with clear messages
3. Push changes: `git push -u origin claude/setup-ragbot-ask-catalyst-i4WeR`
4. Create PR when ready for review

### Code Standards
- Follow PEP 8 for Python code
- Add docstrings to functions and classes
- Write unit tests for new features
- Keep functions focused and modular

## Next Steps
- [ ] Set up rag-bot directory structure
- [ ] Implement document processing pipeline
- [ ] Configure vector database
- [ ] Integrate LLM for generation
- [ ] Add API endpoints for queries
- [ ] Implement testing suite
- [ ] Add monitoring and logging

## Existing Modules

### main.py
Main application entry point and API server.

### operations.py
Core business logic and utility functions.

### mongoDB.py
MongoDB connection and CRUD operations.

### WATI.py
Integration with WATI (WhatsApp Team Inbox) for messaging capabilities.

## API Endpoints (Current)
Document current API endpoints here as they are implemented.

## Testing
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## Deployment
Deployment instructions to be added based on target platform (AWS/GCP/Azure/Heroku).

## Troubleshooting
Common issues and solutions to be documented as they arise.

## Resources
- [RAG Best Practices](https://www.anthropic.com/index/retrieval-augmented-generation)
- MongoDB Documentation
- Vector Database Comparisons

## Contact
Project maintainer information to be added.

---
**Last Updated**: 2026-01-15
**Claude Session**: setup-ragbot-ask-catalyst-i4WeR
