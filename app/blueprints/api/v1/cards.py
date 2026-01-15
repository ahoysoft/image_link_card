"""Card API endpoints."""

from flask import jsonify, request, url_for, g, current_app, abort

from app.blueprints.api.v1 import api_v1_bp
from app.blueprints.api.v1.auth import require_api_key
from app.models.card import Card, CardType
from app.services.storage import get_storage
from app.services.image_processor import ImageProcessor, ImageProcessingError
from app.extensions import db


def card_to_dict(card):
    """Convert a Card model to a dictionary for JSON response."""
    base_url = current_app.config.get('BASE_URL', '')
    return {
        'id': card.id,
        'slug': card.slug,
        'url': f"{base_url}/c/{card.slug}",
        'title': card.title,
        'description': card.description,
        'destination_url': card.destination_url,
        'card_type': card.card_type,
        'image_url': f"{base_url}/i/{card.slug}.png",
        'view_count': card.view_count,
        'created_at': card.created_at.isoformat() + 'Z',
        'updated_at': card.updated_at.isoformat() + 'Z'
    }


@api_v1_bp.route('/cards', methods=['GET'])
@require_api_key
def list_cards():
    """List all cards for the authenticated user.

    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = Card.query.filter_by(user_id=g.current_user.id) \
        .order_by(Card.created_at.desc()) \
        .paginate(page=page, per_page=per_page)

    return jsonify({
        'cards': [card_to_dict(card) for card in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@api_v1_bp.route('/cards', methods=['POST'])
@require_api_key
def create_card():
    """Create a new social card.

    Request (multipart/form-data):
        image: Image file (required)
        title: Card title (required, max 200 chars)
        description: Card description (optional, max 500 chars)
        destination_url: URL to redirect to (required)
        card_type: 'summary' or 'summary_large_image' (optional, default: summary_large_image)
    """
    user = g.current_user

    # Check tier limit
    if not user.can_create_card():
        limit = user.get_monthly_limit()
        return jsonify({
            'error': 'Monthly limit reached',
            'message': f'You have reached your monthly limit of {limit} cards. '
                      f'Upgrade your tier for more.',
            'current_count': user.monthly_card_count,
            'limit': limit
        }), 403

    # Validate required fields
    if 'image' not in request.files:
        return jsonify({
            'error': 'Missing image',
            'message': 'Please provide an image file'
        }), 400

    image_file = request.files['image']
    if not image_file.filename:
        return jsonify({
            'error': 'Empty image',
            'message': 'Please provide a valid image file'
        }), 400

    title = request.form.get('title', '').strip()
    if not title:
        return jsonify({
            'error': 'Missing title',
            'message': 'Please provide a title'
        }), 400
    if len(title) > 200:
        return jsonify({
            'error': 'Title too long',
            'message': 'Title must be 200 characters or less'
        }), 400

    destination_url = request.form.get('destination_url', '').strip()
    if not destination_url:
        return jsonify({
            'error': 'Missing destination_url',
            'message': 'Please provide a destination URL'
        }), 400

    description = request.form.get('description', '').strip()
    if len(description) > 500:
        return jsonify({
            'error': 'Description too long',
            'message': 'Description must be 500 characters or less'
        }), 400

    card_type = request.form.get('card_type', CardType.SUMMARY_LARGE_IMAGE)
    if card_type not in [CardType.SUMMARY, CardType.SUMMARY_LARGE_IMAGE]:
        return jsonify({
            'error': 'Invalid card_type',
            'message': f'card_type must be "{CardType.SUMMARY}" or "{CardType.SUMMARY_LARGE_IMAGE}"'
        }), 400

    # Process image
    processor = ImageProcessor()
    image_data = image_file.read()
    content_type = image_file.content_type or 'application/octet-stream'

    try:
        processor.validate(image_data, content_type)
        processed_data = processor.process(image_data, card_type)
    except ImageProcessingError as e:
        return jsonify({
            'error': 'Image processing failed',
            'message': str(e)
        }), 400

    # Generate slug and storage keys
    slug = Card.generate_slug()
    original_key = f"originals/{user.id}/{slug}.original"
    processed_key = f"processed/{slug}.png"

    # Upload to storage
    storage = get_storage()
    try:
        storage.upload(image_data, original_key, content_type)
        storage.upload(processed_data, processed_key, 'image/png')
    except Exception as e:
        current_app.logger.error(f"Failed to upload image: {e}")
        return jsonify({
            'error': 'Upload failed',
            'message': 'Failed to store image. Please try again.'
        }), 500

    # Create card record
    card = Card(
        user_id=user.id,
        slug=slug,
        title=title,
        description=description or None,
        destination_url=destination_url,
        card_type=card_type,
        image_original_key=original_key,
        image_processed_key=processed_key
    )

    # Increment user's card count
    user.increment_card_count()

    db.session.add(card)
    db.session.commit()

    return jsonify(card_to_dict(card)), 201


@api_v1_bp.route('/cards/<card_id>', methods=['GET'])
@require_api_key
def get_card(card_id):
    """Get a specific card by ID."""
    card = Card.query.filter_by(id=card_id, user_id=g.current_user.id).first()

    if not card:
        abort(404)

    return jsonify(card_to_dict(card))


@api_v1_bp.route('/cards/<card_id>', methods=['PATCH'])
@require_api_key
def update_card(card_id):
    """Update a card's metadata.

    Request (JSON):
        title: New title (optional)
        description: New description (optional)
        destination_url: New destination URL (optional)

    Note: Image cannot be changed. Create a new card instead.
    """
    card = Card.query.filter_by(id=card_id, user_id=g.current_user.id).first()

    if not card:
        abort(404)

    data = request.get_json() or {}

    if 'title' in data:
        title = data['title'].strip()
        if not title:
            return jsonify({
                'error': 'Invalid title',
                'message': 'Title cannot be empty'
            }), 400
        if len(title) > 200:
            return jsonify({
                'error': 'Title too long',
                'message': 'Title must be 200 characters or less'
            }), 400
        card.title = title

    if 'description' in data:
        description = data['description'].strip() if data['description'] else ''
        if len(description) > 500:
            return jsonify({
                'error': 'Description too long',
                'message': 'Description must be 500 characters or less'
            }), 400
        card.description = description or None

    if 'destination_url' in data:
        destination_url = data['destination_url'].strip()
        if not destination_url:
            return jsonify({
                'error': 'Invalid destination_url',
                'message': 'Destination URL cannot be empty'
            }), 400
        card.destination_url = destination_url

    db.session.commit()

    return jsonify(card_to_dict(card))


@api_v1_bp.route('/cards/<card_id>', methods=['DELETE'])
@require_api_key
def delete_card(card_id):
    """Delete a card."""
    card = Card.query.filter_by(id=card_id, user_id=g.current_user.id).first()

    if not card:
        abort(404)

    # Delete images from storage
    storage = get_storage()
    try:
        storage.delete(card.image_original_key)
        storage.delete(card.image_processed_key)
    except Exception as e:
        current_app.logger.warning(f"Failed to delete card images: {e}")

    db.session.delete(card)
    db.session.commit()

    return jsonify({'message': 'Card deleted successfully'}), 200
