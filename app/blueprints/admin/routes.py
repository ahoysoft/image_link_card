"""Admin routes for user and system management."""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps

from app.blueprints.admin import admin_bp
from app.models.user import User, UserTier
from app.models.card import Card
from app.extensions import db


def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users with tier management."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = User.query

    if search:
        query = query.filter(User.email.ilike(f'%{search}%'))

    pagination = query.order_by(User.created_at.desc()) \
        .paginate(page=page, per_page=50)

    return render_template('admin/users.html',
                           users=pagination.items,
                           pagination=pagination,
                           search=search)


@admin_bp.route('/users/<user_id>/tier', methods=['POST'])
@login_required
@admin_required
def update_tier(user_id):
    """Update a user's tier."""
    user = User.query.get_or_404(user_id)
    new_tier = request.form.get('tier')

    if new_tier not in [UserTier.FREE, UserTier.CORE, UserTier.PREMIUM]:
        flash('Invalid tier selected.', 'error')
        return redirect(url_for('admin.users'))

    if user.id == current_user.id:
        flash('You cannot change your own tier.', 'warning')
        return redirect(url_for('admin.users'))

    old_tier = user.tier
    user.tier = new_tier
    db.session.commit()

    flash(f'Updated {user.email} from {old_tier} to {new_tier}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<user_id>/admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user."""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'warning')
        return redirect(url_for('admin.users'))

    user.is_admin = not user.is_admin
    db.session.commit()

    status = 'admin' if user.is_admin else 'regular user'
    flash(f'{user.email} is now a {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/cards')
@login_required
@admin_required
def cards():
    """List all cards in the system."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = Card.query.join(User)

    if search:
        query = query.filter(
            db.or_(
                Card.title.ilike(f'%{search}%'),
                Card.slug.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    pagination = query.order_by(Card.created_at.desc()) \
        .paginate(page=page, per_page=50)

    return render_template('admin/cards.html',
                           cards=pagination.items,
                           pagination=pagination,
                           search=search)


@admin_bp.route('/cards/<card_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_card(card_id):
    """Delete any card (admin only)."""
    from app.services.storage import get_storage

    card = Card.query.get_or_404(card_id)

    # Delete images from storage
    storage = get_storage()
    try:
        storage.delete(card.image_original_key)
        storage.delete(card.image_processed_key)
    except Exception:
        pass

    db.session.delete(card)
    db.session.commit()

    flash('Card deleted successfully.', 'success')
    return redirect(url_for('admin.cards'))


@admin_bp.route('/stats')
@login_required
@admin_required
def stats():
    """System statistics."""
    total_users = User.query.count()
    verified_users = User.query.filter_by(email_verified=True).count()
    total_cards = Card.query.count()
    total_views = db.session.query(db.func.sum(Card.view_count)).scalar() or 0

    tier_counts = db.session.query(
        User.tier,
        db.func.count(User.id)
    ).group_by(User.tier).all()

    return render_template('admin/stats.html',
                           total_users=total_users,
                           verified_users=verified_users,
                           total_cards=total_cards,
                           total_views=total_views,
                           tier_counts=dict(tier_counts))
