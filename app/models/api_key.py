"""API Key model."""

import uuid
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class APIKey(db.Model):
    """API Key model for authenticating API requests."""
    __tablename__ = 'api_keys'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False)
    key_prefix = db.Column(db.String(8), nullable=False)  # First 8 chars for identification
    name = db.Column(db.String(100), nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)

    @classmethod
    def generate_key(cls):
        """Generate a new API key (shown once to user)."""
        return f"sk_{secrets.token_urlsafe(32)}"

    @classmethod
    def create(cls, user_id, name):
        """Create a new API key.

        Returns:
            Tuple of (APIKey instance, raw_key). The raw_key is shown once to the user.
        """
        raw_key = cls.generate_key()
        api_key = cls(
            user_id=user_id,
            name=name,
            key_hash=generate_password_hash(raw_key),
            key_prefix=raw_key[:8]
        )
        return api_key, raw_key

    def verify_key(self, raw_key):
        """Verify a raw key against the stored hash."""
        return check_password_hash(self.key_hash, raw_key)

    @property
    def is_active(self):
        """Check if the API key is active (not revoked)."""
        return self.revoked_at is None

    def revoke(self):
        """Revoke this API key."""
        self.revoked_at = datetime.utcnow()

    def __repr__(self):
        return f'<APIKey {self.key_prefix}... ({self.name})>'
