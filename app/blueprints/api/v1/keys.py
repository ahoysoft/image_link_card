"""API key management endpoints."""

from flask import jsonify, request, g, abort

from app.blueprints.api.v1 import api_v1_bp
from app.blueprints.api.v1.auth import require_api_key
from app.models.api_key import APIKey
from app.extensions import db


def api_key_to_dict(key, include_key=False, raw_key=None):
    """Convert an APIKey model to a dictionary for JSON response."""
    result = {
        'id': key.id,
        'name': key.name,
        'key_prefix': key.key_prefix + '...',
        'created_at': key.created_at.isoformat() + 'Z',
        'last_used_at': key.last_used_at.isoformat() + 'Z' if key.last_used_at else None,
        'is_active': key.is_active
    }

    if include_key and raw_key:
        result['key'] = raw_key

    return result


@api_v1_bp.route('/keys', methods=['GET'])
@require_api_key
def list_keys():
    """List all API keys for the authenticated user.

    Returns active and revoked keys.
    """
    keys = APIKey.query.filter_by(user_id=g.current_user.id) \
        .order_by(APIKey.created_at.desc()) \
        .all()

    return jsonify({
        'keys': [api_key_to_dict(key) for key in keys]
    })


@api_v1_bp.route('/keys', methods=['POST'])
@require_api_key
def create_key():
    """Create a new API key.

    Request (JSON):
        name: Key name/description (required, max 100 chars)

    Returns:
        The new API key. The full key is only shown once!
    """
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    if not name:
        return jsonify({
            'error': 'Missing name',
            'message': 'Please provide a name for the API key'
        }), 400

    if len(name) > 100:
        return jsonify({
            'error': 'Name too long',
            'message': 'Name must be 100 characters or less'
        }), 400

    # Create the API key
    api_key, raw_key = APIKey.create(
        user_id=g.current_user.id,
        name=name
    )

    db.session.add(api_key)
    db.session.commit()

    response = api_key_to_dict(api_key, include_key=True, raw_key=raw_key)
    response['warning'] = 'Save this key now! It will not be shown again.'

    return jsonify(response), 201


@api_v1_bp.route('/keys/<key_id>', methods=['DELETE'])
@require_api_key
def revoke_key(key_id):
    """Revoke an API key.

    The key will no longer be usable for authentication.
    """
    api_key = APIKey.query.filter_by(
        id=key_id,
        user_id=g.current_user.id
    ).first()

    if not api_key:
        abort(404)

    if not api_key.is_active:
        return jsonify({
            'error': 'Key already revoked',
            'message': 'This API key has already been revoked'
        }), 400

    # Don't allow revoking the key being used for this request
    if api_key.id == g.api_key.id:
        return jsonify({
            'error': 'Cannot revoke current key',
            'message': 'You cannot revoke the API key you are currently using'
        }), 400

    api_key.revoke()
    db.session.commit()

    return jsonify({
        'message': 'API key revoked successfully',
        'key': api_key_to_dict(api_key)
    })
