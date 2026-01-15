"""Authentication forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from app.models.user import User


class LoginForm(FlaskForm):
    """Login form."""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')


class RegistrationForm(FlaskForm):
    """User registration form."""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])

    def validate_email(self, field):
        """Check if email is already registered."""
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('This email is already registered.')


class ForgotPasswordForm(FlaskForm):
    """Password reset request form."""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])


class ResetPasswordForm(FlaskForm):
    """Password reset form."""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])


class ChangePasswordForm(FlaskForm):
    """Change password form for logged-in users."""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
