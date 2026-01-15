"""
Azure Function App for Ask Catalyst RAG Bot
Handles HTTP requests and integrates with Azure OpenAI Assistants API
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import azure.functions as func
from assistant_manager import assistant_manager
from vector_store_manager import vector_store_manager
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    logger.info("Health check requested")

    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'assistant': assistant_manager.is_enabled(),
            'vector_store': vector_store_manager.is_enabled(),
            'database': db.is_enabled()
        }
    }

    return func.HttpResponse(
        json.dumps(status),
        mimetype="application/json",
        status_code=200
    )


@app.route(route="query", methods=["POST"])
def query(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle user queries

    Request body:
    {
        "user_id": "user123",
        "message": "What is RAG?",
        "thread_id": "thread_abc" (optional)
    }
    """
    logger.info("Query request received")

    try:
        # Parse request
        req_body = req.get_json()
        user_id = req_body.get('user_id')
        message = req_body.get('message')
        thread_id = req_body.get('thread_id')

        if not user_id or not message:
            return func.HttpResponse(
                json.dumps({'error': 'Missing user_id or message'}),
                mimetype="application/json",
                status_code=400
            )

        # Check if assistant is enabled
        if not assistant_manager.is_enabled():
            return func.HttpResponse(
                json.dumps({'error': 'Assistant service not configured'}),
                mimetype="application/json",
                status_code=503
            )

        # Update user profile
        if db.is_enabled():
            db.create_or_update_user(user_id, {
                'last_message': message,
                'last_query_time': datetime.utcnow().isoformat()
            })

        # Process message
        start_time = datetime.utcnow()
        result = assistant_manager.process_user_message(user_id, message, thread_id)

        if not result['success']:
            # Log error
            if db.is_enabled():
                db.log_analytics_event('query_error', {
                    'user_id': user_id,
                    'error': result.get('error', 'Unknown error')
                })

            return func.HttpResponse(
                json.dumps({
                    'success': False,
                    'error': result.get('error', 'Failed to process message')
                }),
                mimetype="application/json",
                status_code=500
            )

        # Log conversation
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        if db.is_enabled():
            db.log_conversation(user_id, {
                'message': message,
                'response': result.get('response'),
                'thread_id': result.get('thread_id'),
                'citations': result.get('citations', []),
                'processing_time': processing_time,
                'message_type': 'text'
            })

            db.log_analytics_event('query', {
                'user_id': user_id,
                'processing_time': processing_time,
                'has_citations': len(result.get('citations', [])) > 0
            })

        # Return response
        return func.HttpResponse(
            json.dumps({
                'success': True,
                'response': result.get('response'),
                'thread_id': result.get('thread_id'),
                'citations': result.get('citations', []),
                'processing_time': processing_time
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="upload", methods=["POST"])
def upload_documents(req: func.HttpRequest) -> func.HttpResponse:
    """
    Upload documents to vector store

    Request body:
    {
        "file_paths": ["/path/to/doc1.pdf", "/path/to/doc2.txt"]
    }
    """
    logger.info("Document upload request received")

    try:
        # Parse request
        req_body = req.get_json()
        file_paths = req_body.get('file_paths', [])

        if not file_paths:
            return func.HttpResponse(
                json.dumps({'error': 'No file_paths provided'}),
                mimetype="application/json",
                status_code=400
            )

        # Check if vector store is enabled
        if not vector_store_manager.is_enabled():
            return func.HttpResponse(
                json.dumps({'error': 'Vector store service not configured'}),
                mimetype="application/json",
                status_code=503
            )

        # Upload files
        result = vector_store_manager.upload_files(file_paths)

        # Log analytics
        if db.is_enabled():
            db.log_analytics_event('upload', {
                'total_files': result['total'],
                'successful': result['successful'],
                'failed': result['failed']
            })

        return func.HttpResponse(
            json.dumps({
                'success': True,
                **result
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="history/{user_id}", methods=["GET"])
def get_history(req: func.HttpRequest) -> func.HttpResponse:
    """Get conversation history for a user"""
    logger.info("History request received")

    try:
        user_id = req.route_params.get('user_id')
        limit = int(req.params.get('limit', 10))

        if not db.is_enabled():
            return func.HttpResponse(
                json.dumps({'error': 'Database service not configured'}),
                mimetype="application/json",
                status_code=503
            )

        history = db.get_user_conversation_history(user_id, limit)

        return func.HttpResponse(
            json.dumps({
                'success': True,
                'user_id': user_id,
                'history': history,
                'count': len(history)
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="vector-store/info", methods=["GET"])
def vector_store_info(req: func.HttpRequest) -> func.HttpResponse:
    """Get vector store information"""
    logger.info("Vector store info request received")

    try:
        if not vector_store_manager.is_enabled():
            return func.HttpResponse(
                json.dumps({'error': 'Vector store service not configured'}),
                mimetype="application/json",
                status_code=503
            )

        info = vector_store_manager.get_vector_store_info()

        return func.HttpResponse(
            json.dumps({
                'success': True,
                **info
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error getting vector store info: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="analytics", methods=["GET"])
def get_analytics(req: func.HttpRequest) -> func.HttpResponse:
    """Get analytics data"""
    logger.info("Analytics request received")

    try:
        date = req.params.get('date')  # YYYY-MM-DD format

        if not db.is_enabled():
            return func.HttpResponse(
                json.dumps({'error': 'Database service not configured'}),
                mimetype="application/json",
                status_code=503
            )

        analytics = db.get_daily_analytics(date)

        return func.HttpResponse(
            json.dumps({
                'success': True,
                'date': date or datetime.utcnow().strftime('%Y-%m-%d'),
                'events': analytics,
                'count': len(analytics)
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )
