"""Dashboard routes."""

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.blueprints.dashboard import dashboard_bp
from app.blueprints.dashboard.forms import CardForm, CardEditForm, APIKeyForm
from app.models.card import Card, CardType
from app.models.api_key import APIKey
from app.services.storage import get_storage
from app.services.image_processor import ImageProcessor, ImageProcessingError
from app.extensions import db


@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page."""
    cards_count = Card.query.filter_by(user_id=current_user.id).count()
    total_views = db.session.query(db.func.sum(Card.view_count)) \
        .filter(Card.user_id == current_user.id).scalar() or 0
    api_keys_count = APIKey.query.filter_by(
        user_id=current_user.id,
        revoked_at=None
    ).count()

    monthly_limit = current_user.get_monthly_limit()
    monthly_used = current_user.monthly_card_count

    return render_template('dashboard/index.html',
                           cards_count=cards_count,
                           total_views=total_views,
                           api_keys_count=api_keys_count,
                           monthly_limit=monthly_limit,
                           monthly_used=monthly_used)


# Card routes
@dashboard_bp.route('/cards')
@login_required
def cards_list():
    """List user's cards."""
    page = request.args.get('page', 1, type=int)
    pagination = Card.query.filter_by(user_id=current_user.id) \
        .order_by(Card.created_at.desc()) \
        .paginate(page=page, per_page=20)

    return render_template('dashboard/cards/list.html',
                           cards=pagination.items,
                           pagination=pagination)


@dashboard_bp.route('/cards/create', methods=['GET', 'POST'])
@login_required
def cards_create():
    """Create a new card."""
    # Check tier limit
    if not current_user.can_create_card():
        limit = current_user.get_monthly_limit()
        flash(f'You have reached your monthly limit of {limit} cards.', 'warning')
        return redirect(url_for('dashboard.cards_list'))

    form = CardForm()

    if form.validate_on_submit():
        processor = ImageProcessor()
        image_data = form.image.data.read()
        content_type = form.image.data.content_type or 'application/octet-stream'

        try:
            processor.validate(image_data, content_type)
            processed_data = processor.process(image_data, form.card_type.data)
        except ImageProcessingError as e:
            flash(f'Image error: {e}', 'error')
            return render_template('dashboard/cards/create.html', form=form)

        # Generate slug and storage keys
        slug = Card.generate_slug()
        original_key = f"originals/{current_user.id}/{slug}.original"
        processed_key = f"processed/{slug}.png"

        # Upload to storage
        storage = get_storage()
        try:
            storage.upload(image_data, original_key, content_type)
            storage.upload(processed_data, processed_key, 'image/png')
        except Exception as e:
            current_app.logger.error(f"Failed to upload image: {e}")
            flash('Failed to upload image. Please try again.', 'error')
            return render_template('dashboard/cards/create.html', form=form)

        # Create card
        card = Card(
            user_id=current_user.id,
            slug=slug,
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            destination_url=form.destination_url.data.strip(),
            card_type=form.card_type.data,
            image_original_key=original_key,
            image_processed_key=processed_key
        )

        current_user.increment_card_count()
        db.session.add(card)
        db.session.commit()

        flash('Card created successfully!', 'success')
        return redirect(url_for('dashboard.cards_list'))

    return render_template('dashboard/cards/create.html', form=form)


@dashboard_bp.route('/cards/<card_id>/edit', methods=['GET', 'POST'])
@login_required
def cards_edit(card_id):
    """Edit a card."""
    card = Card.query.filter_by(id=card_id, user_id=current_user.id).first_or_404()
    form = CardEditForm(obj=card)

    if form.validate_on_submit():
        card.title = form.title.data.strip()
        card.description = form.description.data.strip() if form.description.data else None
        card.destination_url = form.destination_url.data.strip()
        db.session.commit()

        flash('Card updated successfully!', 'success')
        return redirect(url_for('dashboard.cards_list'))

    return render_template('dashboard/cards/edit.html', form=form, card=card)


@dashboard_bp.route('/cards/<card_id>/delete', methods=['POST'])
@login_required
def cards_delete(card_id):
    """Delete a card."""
    card = Card.query.filter_by(id=card_id, user_id=current_user.id).first_or_404()

    # Delete images from storage
    storage = get_storage()
    try:
        storage.delete(card.image_original_key)
        storage.delete(card.image_processed_key)
    except Exception as e:
        current_app.logger.warning(f"Failed to delete card images: {e}")

    db.session.delete(card)
    db.session.commit()

    flash('Card deleted successfully!', 'success')
    return redirect(url_for('dashboard.cards_list'))


# API Key routes
@dashboard_bp.route('/api-keys')
@login_required
def api_keys():
    """List user's API keys."""
    keys = APIKey.query.filter_by(user_id=current_user.id) \
        .order_by(APIKey.created_at.desc()).all()

    # Check for newly created key in session
    new_key = request.args.get('new_key')

    return render_template('dashboard/api_keys/list.html',
                           keys=keys,
                           new_key=new_key)


@dashboard_bp.route('/api-keys/create', methods=['POST'])
@login_required
def api_keys_create():
    """Create a new API key."""
    form = APIKeyForm()

    if form.validate_on_submit():
        api_key, raw_key = APIKey.create(
            user_id=current_user.id,
            name=form.name.data.strip()
        )
        db.session.add(api_key)
        db.session.commit()

        flash('API key created! Copy it now - it won\'t be shown again.', 'success')
        return redirect(url_for('dashboard.api_keys', new_key=raw_key))

    flash('Please provide a name for the API key.', 'error')
    return redirect(url_for('dashboard.api_keys'))


@dashboard_bp.route('/api-keys/<key_id>/revoke', methods=['POST'])
@login_required
def api_keys_revoke(key_id):
    """Revoke an API key."""
    api_key = APIKey.query.filter_by(
        id=key_id,
        user_id=current_user.id
    ).first_or_404()

    if not api_key.is_active:
        flash('This key has already been revoked.', 'warning')
        return redirect(url_for('dashboard.api_keys'))

    api_key.revoke()
    db.session.commit()

    flash('API key revoked successfully.', 'success')
    return redirect(url_for('dashboard.api_keys'))


# Settings
@dashboard_bp.route('/settings')
@login_required
def settings():
    """Account settings page."""
    return render_template('dashboard/settings.html')
