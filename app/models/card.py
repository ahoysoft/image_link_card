"""Card model for social link previews."""

import uuid
from datetime import datetime
from nanoid import generate

from app.extensions import db


class CardType:
    """Card type constants."""
    SUMMARY = 'summary'
    SUMMARY_LARGE_IMAGE = 'summary_large_image'


class Card(db.Model):
    """Social card model."""
    __tablename__ = 'cards'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    slug = db.Column(db.String(21), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    destination_url = db.Column(db.String(2048), nullable=False)
    card_type = db.Column(db.String(30), default=CardType.SUMMARY_LARGE_IMAGE)
    image_original_key = db.Column(db.String(255), nullable=False)  # R2/storage object key
    image_processed_key = db.Column(db.String(255), nullable=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_slug():
        """Generate a URL-safe nanoid slug."""
        return generate(size=21)

    def increment_views(self):
        """Increment view count (for non-bot visits)."""
        self.view_count += 1

    def __repr__(self):
        return f'<Card {self.slug}: {self.title[:30]}>'
