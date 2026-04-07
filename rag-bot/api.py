"""
Flask API for Ask Catalyst RAG Bot
Provides REST endpoints for document ingestion and querying
Compatible with Azure OpenAI Assistants API
"""
from flask import Flask, request, jsonify
import logging
from datetime import datetime
from assistant_manager import assistant_manager
from vector_store_manager import vector_store_manager
from database import db
from whatsapp_handler import whatsapp_handler
from auth import require_api_key, is_exempt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'assistant': assistant_manager.is_enabled(),
            'vector_store': vector_store_manager.is_enabled(),
            'database': db.is_enabled(),
            'whatsapp': whatsapp_handler.is_enabled()
        }
    }), 200


@app.route('/api/query', methods=['POST'])
@require_api_key
def query():
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
        data = request.get_json()
        user_id = data.get('user_id')
        message = data.get('message')
        thread_id = data.get('thread_id')

        if not user_id or not message:
            return jsonify({'error': 'Missing user_id or message'}), 400

        # Check if assistant is enabled
        if not assistant_manager.is_enabled():
            return jsonify({'error': 'Assistant service not configured'}), 503

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

            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to process message')
            }), 500

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
        return jsonify({
            'success': True,
            'response': result.get('response'),
            'thread_id': result.get('thread_id'),
            'citations': result.get('citations', []),
            'processing_time': processing_time
        }), 200

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
@require_api_key
def upload_documents():
    """
    Upload documents to vector store

    Request body:
    {
        "file_paths": ["/path/to/doc1.pdf", "/path/to/doc2.txt"]
    }
    """
    logger.info("Document upload request received")

    try:
        data = request.get_json()
        file_paths = data.get('file_paths', [])

        if not file_paths:
            return jsonify({'error': 'No file_paths provided'}), 400

        # Check if vector store is enabled
        if not vector_store_manager.is_enabled():
            return jsonify({'error': 'Vector store service not configured'}), 503

        # Upload files
        result = vector_store_manager.upload_files(file_paths)

        # Log analytics
        if db.is_enabled():
            db.log_analytics_event('upload', {
                'total_files': result['total'],
                'successful': result['successful'],
                'failed': result['failed']
            })

        return jsonify({
            'success': True,
            **result
        }), 200

    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<user_id>', methods=['GET'])
@require_api_key
def get_history(user_id):
    """Get conversation history for a user"""
    logger.info(f"History request received for user {user_id}")

    try:
        limit = int(request.args.get('limit', 10))

        if not db.is_enabled():
            return jsonify({'error': 'Database service not configured'}), 503

        history = db.get_user_conversation_history(user_id, limit)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'history': history,
            'count': len(history)
        }), 200

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/vector-store/info', methods=['GET'])
@require_api_key
def vector_store_info():
    """Get vector store information"""
    logger.info("Vector store info request received")

    try:
        if not vector_store_manager.is_enabled():
            return jsonify({'error': 'Vector store service not configured'}), 503

        info = vector_store_manager.get_vector_store_info()

        return jsonify({
            'success': True,
            **info
        }), 200

    except Exception as e:
        logger.error(f"Error getting vector store info: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/vector-store/files', methods=['GET'])
@require_api_key
def list_files():
    """List all files in vector store"""
    logger.info("List files request received")

    try:
        if not vector_store_manager.is_enabled():
            return jsonify({'error': 'Vector store service not configured'}), 503

        files = vector_store_manager.list_files()

        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        }), 200

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/vector-store/files/<file_id>', methods=['DELETE'])
@require_api_key
def delete_file(file_id):
    """Delete a file from vector store"""
    logger.info(f"Delete file request received for {file_id}")

    try:
        if not vector_store_manager.is_enabled():
            return jsonify({'error': 'Vector store service not configured'}), 503

        success = vector_store_manager.delete_file(file_id)

        if success:
            return jsonify({
                'success': True,
                'message': f'File {file_id} deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete file'
            }), 500

    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics', methods=['GET'])
@require_api_key
def get_analytics():
    """Get analytics data"""
    logger.info("Analytics request received")

    try:
        date = request.args.get('date')  # YYYY-MM-DD format

        if not db.is_enabled():
            return jsonify({'error': 'Database service not configured'}), 503

        analytics = db.get_daily_analytics(date)

        return jsonify({
            'success': True,
            'date': date or datetime.utcnow().strftime('%Y-%m-%d'),
            'events': analytics,
            'count': len(analytics)
        }), 200

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/<user_id>', methods=['GET'])
@require_api_key
def get_user_profile(user_id):
    """Get user profile"""
    logger.info(f"User profile request for {user_id}")

    try:
        if not db.is_enabled():
            return jsonify({'error': 'Database service not configured'}), 503

        profile = db.get_user_profile(user_id)

        if profile:
            return jsonify({
                'success': True,
                'profile': profile
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/webhook/whatsapp', methods=['GET', 'POST'])
def whatsapp_webhook():
    """
    WhatsApp Cloud API webhook endpoint

    GET: Webhook verification
    POST: Incoming messages
    """
    logger.info("WhatsApp webhook request received")

    try:
        if request.method == 'GET':
            # Webhook verification
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')

            if not all([mode, token, challenge]):
                return jsonify({'error': 'Missing verification parameters'}), 400

            result = whatsapp_handler.verify_webhook(mode, token, challenge)

            if result:
                logger.info("WhatsApp webhook verified")
                return result, 200
            else:
                logger.warning("WhatsApp webhook verification failed")
                return jsonify({'error': 'Verification failed'}), 403

        elif request.method == 'POST':
            # Verify signature
            signature = request.headers.get('X-Hub-Signature-256', '')
            if signature and not whatsapp_handler.verify_signature(request.data, signature):
                logger.warning("Invalid webhook signature")
                return jsonify({'error': 'Invalid signature'}), 403

            # Process webhook
            webhook_data = request.get_json()

            if not webhook_data:
                return jsonify({'error': 'Invalid request body'}), 400

            # Process in background (return 200 immediately)
            result = whatsapp_handler.process_webhook(webhook_data)

            # Always return 200 to acknowledge receipt
            return jsonify({'status': 'received'}), 200

    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        # Still return 200 to avoid webhook retry storms
        return jsonify({'status': 'error', 'message': str(e)}), 200


@app.route('/api/whatsapp/send', methods=['POST'])
@require_api_key
def send_whatsapp_message():
    """
    Send a WhatsApp message manually

    Request body:
    {
        "phone_number": "1234567890",
        "message": "Hello from Ask Catalyst!"
    }
    """
    logger.info("Manual WhatsApp send request")

    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message')

        if not phone_number or not message:
            return jsonify({'error': 'Missing phone_number or message'}), 400

        if not whatsapp_handler.is_enabled():
            return jsonify({'error': 'WhatsApp not configured'}), 503

        success = whatsapp_handler.send_text_message(phone_number, message)

        if success:
            return jsonify({
                'success': True,
                'message': 'Message sent successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send message'
            }), 500

    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/whatsapp/welcome', methods=['POST'])
@require_api_key
def send_welcome_whatsapp():
    """
    Send welcome message to a WhatsApp user

    Request body:
    {
        "phone_number": "1234567890",
        "name": "John" (optional)
    }
    """
    logger.info("WhatsApp welcome message request")

    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        name = data.get('name')

        if not phone_number:
            return jsonify({'error': 'Missing phone_number'}), 400

        if not whatsapp_handler.is_enabled():
            return jsonify({'error': 'WhatsApp not configured'}), 503

        success = whatsapp_handler.send_welcome_message(phone_number, name)

        if success:
            return jsonify({
                'success': True,
                'message': 'Welcome message sent'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send welcome message'
            }), 500

    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os

    # Run the app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting Ask Catalyst RAG Bot API on port {port}")
    logger.info(f"Services status:")
    logger.info(f"  - Assistant: {'✓' if assistant_manager.is_enabled() else '✗'}")
    logger.info(f"  - Vector Store: {'✓' if vector_store_manager.is_enabled() else '✗'}")
    logger.info(f"  - Database: {'✓' if db.is_enabled() else '✗'}")
    logger.info(f"  - WhatsApp: {'✓' if whatsapp_handler.is_enabled() else '✗'}")

    app.run(host='0.0.0.0', port=port, debug=debug)
