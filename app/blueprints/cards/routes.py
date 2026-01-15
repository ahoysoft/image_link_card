"""Public card serving routes."""

from flask import render_template, redirect, request, abort, send_file, Response, current_app
from io import BytesIO

from app.blueprints.cards import cards_bp
from app.models.card import Card
from app.services.storage import get_storage
from app.utils.bot_detection import is_bot
from app.extensions import db


@cards_bp.route('/c/<slug>')
def serve_card(slug):
    """Serve a social card.

    For bots/crawlers: Returns HTML with meta tags
    For regular users: Redirects to destination URL
    """
    card = Card.query.filter_by(slug=slug).first()

    if not card:
        abort(404)

    user_agent = request.headers.get('User-Agent', '')

    if is_bot(user_agent):
        # Serve meta tags HTML for social media crawlers
        return render_template('cards/meta.html', card=card)

    # Increment view count for real users
    card.increment_views()
    db.session.commit()

    # Redirect to destination
    return redirect(card.destination_url, code=302)


@cards_bp.route('/i/<slug>.png')
def serve_image(slug):
    """Serve the processed card image.

    This endpoint is referenced in the meta tags and serves the
    optimized image to social media crawlers.
    """
    card = Card.query.filter_by(slug=slug).first()

    if not card:
        abort(404)

    storage = get_storage()

    # For R2 storage, redirect to the public URL
    if current_app.config.get('STORAGE_BACKEND') == 'r2':
        return redirect(storage.get_url(card.image_processed_key))

    # For local storage, serve the file directly
    try:
        image_data = storage.download(card.image_processed_key)
        return Response(
            image_data,
            mimetype='image/png',
            headers={
                'Cache-Control': 'public, max-age=86400',  # Cache for 1 day
                'Content-Disposition': f'inline; filename={slug}.png'
            }
        )
    except Exception as e:
        current_app.logger.error(f"Failed to serve image {slug}: {e}")
        abort(404)
