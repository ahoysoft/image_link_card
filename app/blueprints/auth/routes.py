"""Authentication routes."""

import secrets
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import (
    LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
)
from app.models.user import User, OAuthAccount
from app.extensions import db
from app.services.email_service import email_service


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if user and user.check_password(form.password.data):
            if not user.email_verified:
                flash('Please verify your email address before logging in.', 'warning')
                return redirect(url_for('auth.login'))

            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')

            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))

        flash('Invalid email or password.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Create verification token
        verification_token = secrets.token_urlsafe(32)

        user = User(
            email=form.email.data.lower(),
            email_verification_token=verification_token
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # Send verification email
        verification_url = url_for(
            'auth.verify_email',
            token=verification_token,
            _external=True
        )
        email_service.send_verification_email(user.email, verification_url)

        flash('Account created! Please check your email to verify your address.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify user's email address."""
    user = User.query.filter_by(email_verification_token=token).first()

    if not user:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('auth.login'))

    if user.email_verified:
        flash('Email already verified.', 'info')
        return redirect(url_for('auth.login'))

    user.email_verified = True
    user.email_verification_token = None
    db.session.commit()

    # Send welcome email
    email_service.send_welcome_email(user.email)

    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email."""
    email = request.form.get('email', '').lower()

    if not email:
        flash('Please provide an email address.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()

    if user and not user.email_verified:
        # Generate new token
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        db.session.commit()

        verification_url = url_for(
            'auth.verify_email',
            token=verification_token,
            _external=True
        )
        email_service.send_verification_email(user.email, verification_url)

    # Always show success message to prevent email enumeration
    flash('If an account exists with that email, a verification link has been sent.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if user and user.email_verified:
            # Generate reset token (reusing verification token field)
            reset_token = secrets.token_urlsafe(32)
            user.email_verification_token = f"reset:{reset_token}"
            db.session.commit()

            reset_url = url_for(
                'auth.reset_password',
                token=reset_token,
                _external=True
            )
            email_service.send_password_reset(user.email, reset_url)

        # Always show success to prevent email enumeration
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password using token."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    # Find user with this reset token
    user = User.query.filter_by(email_verification_token=f"reset:{token}").first()

    if not user:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.email_verification_token = None
        db.session.commit()

        flash('Password reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/google')
def google_login():
    """Initiate Google OAuth login."""
    from flask_dance.contrib.google import google

    if not google.authorized:
        return redirect(url_for('google.login'))

    return redirect(url_for('auth.google_callback'))


@auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    from flask_dance.contrib.google import google

    if not google.authorized:
        flash('Failed to authenticate with Google.', 'error')
        return redirect(url_for('auth.login'))

    try:
        resp = google.get('/oauth2/v1/userinfo')
        if not resp.ok:
            flash('Failed to get user info from Google.', 'error')
            return redirect(url_for('auth.login'))

        google_info = resp.json()
        google_user_id = google_info['id']
        email = google_info.get('email', '').lower()

        if not email:
            flash('Could not get email from Google.', 'error')
            return redirect(url_for('auth.login'))

        # Check if OAuth account exists
        oauth_account = OAuthAccount.query.filter_by(
            provider='google',
            provider_user_id=google_user_id
        ).first()

        if oauth_account:
            # Existing OAuth account - log in
            login_user(oauth_account.user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard.index'))

        # Check if user with this email exists
        user = User.query.filter_by(email=email).first()

        if user:
            # Link OAuth to existing account
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider='google',
                provider_user_id=google_user_id
            )
            db.session.add(oauth_account)
            db.session.commit()

            login_user(user)
            flash('Google account linked and logged in!', 'success')
            return redirect(url_for('dashboard.index'))

        # Create new user with OAuth
        user = User(
            email=email,
            email_verified=True  # Google emails are verified
        )
        db.session.add(user)
        db.session.flush()

        oauth_account = OAuthAccount(
            user_id=user.id,
            provider='google',
            provider_user_id=google_user_id
        )
        db.session.add(oauth_account)
        db.session.commit()

        login_user(user)
        flash('Account created and logged in!', 'success')
        return redirect(url_for('dashboard.index'))

    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {e}")
        flash('An error occurred during authentication.', 'error')
        return redirect(url_for('auth.login'))
