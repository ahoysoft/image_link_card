"""API v1 blueprint."""

from flask import Blueprint

api_v1_bp = Blueprint('api_v1', __name__)

# Register error handlers
from app.blueprints.api.errors import register_api_error_handlers
register_api_error_handlers(api_v1_bp)

# Import routes
from app.blueprints.api.v1 import cards, keys  # noqa: E402, F401
