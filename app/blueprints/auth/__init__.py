"""Authentication blueprint with Google OAuth support."""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from app.blueprints.auth import routes  # noqa: E402, F401


def init_oauth(app):
    """Initialize OAuth providers.

    This should be called from the application factory after the app is created.
    """
    from flask_dance.contrib.google import make_google_blueprint

    # Only set up OAuth if credentials are configured
    google_client_id = app.config.get('GOOGLE_CLIENT_ID')
    google_client_secret = app.config.get('GOOGLE_CLIENT_SECRET')

    if google_client_id and google_client_secret:
        google_bp = make_google_blueprint(
            client_id=google_client_id,
            client_secret=google_client_secret,
            scope=['email'],
            redirect_to='auth.google_callback'
        )
        app.register_blueprint(google_bp, url_prefix='/oauth')
