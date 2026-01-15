"""Dashboard forms."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, URLField, SelectField
from wtforms.validators import DataRequired, Length, URL, Optional


class CardForm(FlaskForm):
    """Form for creating a new card."""
    image = FileField('Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    title = StringField('Title', validators=[
        DataRequired(),
        Length(max=200, message='Title must be 200 characters or less.')
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message='Description must be 500 characters or less.')
    ])
    destination_url = URLField('Destination URL', validators=[
        DataRequired(),
        URL(message='Please enter a valid URL.')
    ])
    card_type = SelectField('Card Type', choices=[
        ('summary_large_image', 'Large Image (1200x628) - Recommended'),
        ('summary', 'Summary (144x144)')
    ])


class CardEditForm(FlaskForm):
    """Form for editing a card (image cannot be changed)."""
    title = StringField('Title', validators=[
        DataRequired(),
        Length(max=200, message='Title must be 200 characters or less.')
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message='Description must be 500 characters or less.')
    ])
    destination_url = URLField('Destination URL', validators=[
        DataRequired(),
        URL(message='Please enter a valid URL.')
    ])


class APIKeyForm(FlaskForm):
    """Form for creating an API key."""
    name = StringField('Key Name', validators=[
        DataRequired(),
        Length(max=100, message='Name must be 100 characters or less.')
    ])
