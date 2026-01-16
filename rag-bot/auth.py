"""
Authentication middleware for Ask Catalyst API
Implements API key-based authentication
"""
import os
import secrets
import logging
from functools import wraps
from flask import request, jsonify
import azure.functions as func

logger = logging.getLogger(__name__)

# API Keys configuration (in production, use Azure Key Vault)
API_KEYS = set()

def load_api_keys():
    """Load API keys from environment"""
    global API_KEYS
    # Primary API key
    primary_key = os.getenv('API_KEY')
    if primary_key:
        API_KEYS.add(primary_key)

    # Secondary API key (for rotation)
    secondary_key = os.getenv('API_KEY_SECONDARY')
    if secondary_key:
        API_KEYS.add(secondary_key)

    if not API_KEYS:
        logger.error("No API keys configured! All API endpoints will reject requests.")
        logger.error("Set API_KEY environment variable immediately.")

# Load keys on module import
load_api_keys()

def generate_api_key():
    """Generate a secure random API key"""
    return secrets.token_urlsafe(32)

def require_api_key(f):
    """
    Decorator to require API key authentication for Flask routes

    Usage:
        @app.route('/api/query')
        @require_api_key
        def query():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if not api_key:
            logger.warning(f"API request to {request.path} without API key")
            return jsonify({
                'error': 'Missing API key',
                'message': 'Provide API key in X-API-Key header or api_key query parameter'
            }), 401

        if api_key not in API_KEYS:
            logger.warning(f"Invalid API key attempt for {request.path}")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 403

        # API key is valid, proceed with request
        return f(*args, **kwargs)

    return decorated_function

def verify_api_key_azure(req: func.HttpRequest) -> tuple[bool, str]:
    """
    Verify API key for Azure Functions

    Returns:
        (is_valid, error_message)
    """
    # Get API key from header or query parameter
    api_key = req.headers.get('X-API-Key') or req.params.get('api_key')

    if not api_key:
        return False, 'Missing API key. Provide in X-API-Key header or api_key query parameter'

    if api_key not in API_KEYS:
        logger.warning(f"Invalid API key attempt for {req.url}")
        return False, 'Invalid API key'

    return True, ''

# Exempt endpoints (don't require API key)
EXEMPT_ENDPOINTS = {
    '/health',  # Health check should be public
    '/webhook/whatsapp',  # Webhook uses signature verification instead
}

def is_exempt(path: str) -> bool:
    """Check if endpoint is exempt from API key requirement"""
    return path in EXEMPT_ENDPOINTS
