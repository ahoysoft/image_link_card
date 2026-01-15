"""Public card serving blueprint."""

from flask import Blueprint

cards_bp = Blueprint('cards', __name__)

from app.blueprints.cards import routes  # noqa: E402, F401
