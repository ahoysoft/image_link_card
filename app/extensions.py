"""Flask extensions instantiated here to avoid circular imports."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Database
db = SQLAlchemy()
migrate = Migrate()

# Authentication
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Security
csrf = CSRFProtect()
