"""User and OAuth account models."""

import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app

from app.extensions import db


class UserTier:
    """User subscription tiers."""
    FREE = 'free'
    CORE = 'core'
    PREMIUM = 'premium'


class User(UserMixin, db.Model):
    """User model."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth-only users
    tier = db.Column(db.String(20), default=UserTier.FREE, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), nullable=True)
    monthly_card_count = db.Column(db.Integer, default=0)
    card_count_reset_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    oauth_accounts = db.relationship('OAuthAccount', backref='user', lazy='dynamic',
                                     cascade='all, delete-orphan')
    api_keys = db.relationship('APIKey', backref='user', lazy='dynamic',
                               cascade='all, delete-orphan')
    cards = db.relationship('Card', backref='user', lazy='dynamic',
                            cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user's password."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_monthly_limit(self):
        """Get the user's monthly card creation limit based on tier."""
        limits = current_app.config.get('TIER_LIMITS', {})
        return limits.get(self.tier, 5)

    def can_create_card(self):
        """Check if user can create a new card this month."""
        self._maybe_reset_monthly_count()
        return self.monthly_card_count < self.get_monthly_limit()

    def increment_card_count(self):
        """Increment the monthly card count."""
        self._maybe_reset_monthly_count()
        self.monthly_card_count += 1

    def _maybe_reset_monthly_count(self):
        """Reset monthly count if we're in a new month."""
        now = datetime.utcnow()
        if (self.card_count_reset_at is None or
            self.card_count_reset_at.year != now.year or
            self.card_count_reset_at.month != now.month):
            self.monthly_card_count = 0
            self.card_count_reset_at = now

    def __repr__(self):
        return f'<User {self.email}>'


class OAuthAccount(db.Model):
    """OAuth account linked to a user."""
    __tablename__ = 'oauth_accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # 'google'
    provider_user_id = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_user_id', name='uq_oauth_provider_user'),
    )

    def __repr__(self):
        return f'<OAuthAccount {self.provider}:{self.provider_user_id}>'
