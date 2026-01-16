"""Application factory for the Social Card Service."""

import os
from flask import Flask

from app.config import config
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration to use ('development', 'production', 'testing').
                    Defaults to FLASK_ENV environment variable or 'development'.

    Returns:
        Configured Flask application instance.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Create upload directory for local storage
    if app.config.get('STORAGE_BACKEND') == 'local':
        upload_path = app.config.get('LOCAL_STORAGE_PATH', 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        os.makedirs(os.path.join(upload_path, 'originals'), exist_ok=True)
        os.makedirs(os.path.join(upload_path, 'processed'), exist_ok=True)

    # Register blueprints
    register_blueprints(app)

    # Initialize OAuth
    from app.blueprints.auth import init_oauth
    init_oauth(app)

    # Register error handlers
    register_error_handlers(app)

    # Setup user loader for Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    return app


def register_blueprints(app):
    """Register all application blueprints."""
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.api.v1 import api_v1_bp
    from app.blueprints.cards import cards_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    app.register_blueprint(cards_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Exempt API from CSRF protection (uses API key auth instead)
    csrf.exempt(api_v1_bp)

    # Landing page route
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('public/landing.html')

    # Serve local uploads in development
    if app.config.get('STORAGE_BACKEND') == 'local':
        from flask import send_from_directory

        @app.route('/uploads/<path:filename>')
        def serve_upload(filename):
            upload_path = app.config.get('LOCAL_STORAGE_PATH', 'uploads')
            return send_from_directory(upload_path, filename)


def register_error_handlers(app):
    """Register error handlers for the application."""
    from flask import render_template, request, jsonify

    def is_api_request():
        return request.path.startswith('/api/')

    @app.errorhandler(404)
    def not_found_error(error):
        if is_api_request():
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if is_api_request():
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
