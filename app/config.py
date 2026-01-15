import os
from datetime import timedelta


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')

    # Fix for Render PostgreSQL URLs (postgres:// -> postgresql://)
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    # R2 Storage
    R2_ACCOUNT_ID = os.environ.get('R2_ACCOUNT_ID')
    R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID')
    R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
    R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME', 'social-cards')
    R2_PUBLIC_URL = os.environ.get('R2_PUBLIC_URL')

    # Email (Resend)
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    MAIL_FROM = os.environ.get('MAIL_FROM', 'noreply@example.com')

    # OAuth - Google
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # App
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Tier limits (monthly card creation)
    TIER_LIMITS = {
        'free': 5,
        'core': 50,      # TBD - placeholder
        'premium': 500,  # TBD - placeholder
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    STORAGE_BACKEND = 'local'
    LOCAL_STORAGE_PATH = 'uploads'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    STORAGE_BACKEND = 'r2'

    # Enforce HTTPS in production
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    STORAGE_BACKEND = 'local'
    LOCAL_STORAGE_PATH = 'test_uploads'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
