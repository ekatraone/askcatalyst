"""
Flask API for RAG Bot
Provides REST endpoints for document ingestion and querying
"""
from flask import Flask, request, jsonify
import logging
from typing import Dict, Any
from rag_pipeline import RAGPipeline
from config import RAGConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize RAG pipeline
config = RAGConfig()
pipeline = RAGPipeline(config)

# Store initialization status
initialized = False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'initialized': initialized
    }), 200


@app.route('/api/ingest', methods=['POST'])
def ingest_documents():
    """
    Ingest documents into the RAG system

    Body:
    {
        "file_paths": ["path/to/doc1.txt", "path/to/doc2.txt"]
    }
    """
    try:
        data = request.get_json()

        if not data or 'file_paths' not in data:
            return jsonify({
                'error': 'Missing file_paths in request body'
            }), 400

        file_paths = data['file_paths']

        if not isinstance(file_paths, list):
            return jsonify({
                'error': 'file_paths must be a list'
            }), 400

        # Ingest documents
        num_chunks = pipeline.ingest_documents(file_paths)

        global initialized
        initialized = True

        return jsonify({
            'success': True,
            'num_documents': len(file_paths),
            'num_chunks': num_chunks,
            'message': f'Successfully ingested {len(file_paths)} documents'
        }), 200

    except Exception as e:
        logger.error(f"Error ingesting documents: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/query', methods=['POST'])
def query():
    """
    Query the RAG system

    Body:
    {
        "question": "What is RAG?",
        "include_sources": true
    }
    """
    try:
        data = request.get_json()

        if not data or 'question' not in data:
            return jsonify({
                'error': 'Missing question in request body'
            }), 400

        question = data['question']
        include_sources = data.get('include_sources', True)

        if not initialized:
            return jsonify({
                'error': 'System not initialized. Please ingest documents first.'
            }), 400

        # Query the system
        response = pipeline.query(question, include_sources=include_sources)

        return jsonify({
            'success': True,
            **response
        }), 200

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/add-document', methods=['POST'])
def add_document():
    """
    Add a single document

    Body:
    {
        "file_path": "path/to/document.txt"
    }
    """
    try:
        data = request.get_json()

        if not data or 'file_path' not in data:
            return jsonify({
                'error': 'Missing file_path in request body'
            }), 400

        file_path = data['file_path']

        # Add document
        success = pipeline.add_document(file_path)

        if success:
            global initialized
            initialized = True

            return jsonify({
                'success': True,
                'message': f'Successfully added document: {file_path}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to add document: {file_path}'
            }), 400

    except Exception as e:
        logger.error(f"Error adding document: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/save-index', methods=['POST'])
def save_index():
    """
    Save the vector index

    Body:
    {
        "path": "my_index.faiss"
    }
    """
    try:
        data = request.get_json()
        path = data.get('path', 'index.faiss')

        pipeline.save_index(path)

        return jsonify({
            'success': True,
            'message': f'Index saved to {path}'
        }), 200

    except Exception as e:
        logger.error(f"Error saving index: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/load-index', methods=['POST'])
def load_index():
    """
    Load the vector index

    Body:
    {
        "path": "my_index.faiss"
    }
    """
    try:
        data = request.get_json()
        path = data.get('path', 'index.faiss')

        pipeline.load_index(path)

        global initialized
        initialized = True

        return jsonify({
            'success': True,
            'message': f'Index loaded from {path}'
        }), 200

    except Exception as e:
        logger.error(f"Error loading index: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'embedding_model': config.embedding_model,
        'llm_model': config.llm_model,
        'chunk_size': config.chunk_size,
        'chunk_overlap': config.chunk_overlap,
        'top_k': config.top_k,
        'similarity_threshold': config.similarity_threshold,
        'vector_store_type': config.vector_store_type
    }), 200


if __name__ == '__main__':
    import os

    # Run the app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting RAG Bot API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
