"""API authentication utilities."""

from functools import wraps
from datetime import datetime
from flask import request, jsonify, g

from app.models.api_key import APIKey
from app.extensions import db


def require_api_key(f):
    """Decorator to require API key authentication.

    The API key should be provided in the X-API-Key header.
    On success, sets g.current_user and g.api_key.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({
                'error': 'Missing API key',
                'message': 'Please provide an API key in the X-API-Key header'
            }), 401

        # Find key by prefix (first 8 chars) then verify full key
        prefix = api_key[:8] if len(api_key) >= 8 else api_key
        key_record = APIKey.query.filter_by(
            key_prefix=prefix,
            revoked_at=None
        ).first()

        if not key_record or not key_record.verify_key(api_key):
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid or has been revoked'
            }), 401

        # Check if user's email is verified
        if not key_record.user.email_verified:
            return jsonify({
                'error': 'Email not verified',
                'message': 'Please verify your email address before using the API'
            }), 403

        # Update last used timestamp
        key_record.last_used_at = datetime.utcnow()
        db.session.commit()

        # Set current user and API key in request context
        g.current_user = key_record.user
        g.api_key = key_record

        return f(*args, **kwargs)

    return decorated


def get_current_user():
    """Get the current authenticated user from request context."""
    return getattr(g, 'current_user', None)
