"""Email service using Resend."""

import resend
from flask import current_app, render_template_string


class EmailService:
    """Service for sending transactional emails via Resend."""

    def __init__(self, api_key: str = None, from_address: str = None):
        self.api_key = api_key
        self.from_address = from_address

    def _get_config(self):
        """Get configuration from current app or instance."""
        api_key = self.api_key or current_app.config.get('RESEND_API_KEY')
        from_address = self.from_address or current_app.config.get('MAIL_FROM', 'noreply@example.com')
        return api_key, from_address

    def send_verification_email(self, to_email: str, verification_url: str) -> bool:
        """Send email verification link.

        Args:
            to_email: Recipient email address
            verification_url: URL to verify email

        Returns:
            True if sent successfully
        """
        api_key, from_address = self._get_config()

        if not api_key:
            current_app.logger.warning("RESEND_API_KEY not configured, skipping email")
            return False

        resend.api_key = api_key

        html = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px;">
            <h2>Verify your email address</h2>
            <p>Click the button below to verify your email address and activate your account:</p>
            <p style="margin: 30px 0;">
                <a href="{verification_url}"
                   style="background-color: #2563eb; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Verify Email
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="color: #666; word-break: break-all;">{verification_url}</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 12px;">
                If you didn't create an account, you can safely ignore this email.
            </p>
        </body>
        </html>
        """

        try:
            resend.Emails.send({
                "from": from_address,
                "to": to_email,
                "subject": "Verify your email - Social Card Service",
                "html": html
            })
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {e}")
            return False

    def send_password_reset(self, to_email: str, reset_url: str) -> bool:
        """Send password reset link.

        Args:
            to_email: Recipient email address
            reset_url: URL to reset password

        Returns:
            True if sent successfully
        """
        api_key, from_address = self._get_config()

        if not api_key:
            current_app.logger.warning("RESEND_API_KEY not configured, skipping email")
            return False

        resend.api_key = api_key

        html = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px;">
            <h2>Reset your password</h2>
            <p>Click the button below to reset your password:</p>
            <p style="margin: 30px 0;">
                <a href="{reset_url}"
                   style="background-color: #2563eb; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="color: #666; word-break: break-all;">{reset_url}</p>
            <p style="color: #999;">This link will expire in 1 hour.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 12px;">
                If you didn't request a password reset, you can safely ignore this email.
            </p>
        </body>
        </html>
        """

        try:
            resend.Emails.send({
                "from": from_address,
                "to": to_email,
                "subject": "Reset your password - Social Card Service",
                "html": html
            })
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email: {e}")
            return False

    def send_welcome_email(self, to_email: str) -> bool:
        """Send welcome email after verification.

        Args:
            to_email: Recipient email address

        Returns:
            True if sent successfully
        """
        api_key, from_address = self._get_config()

        if not api_key:
            return False

        resend.api_key = api_key
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')

        html = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px;">
            <h2>Welcome to Social Card Service!</h2>
            <p>Your email has been verified and your account is ready to use.</p>
            <p>You're on the <strong>Free tier</strong> which includes 5 social cards per month.</p>
            <p style="margin: 30px 0;">
                <a href="{base_url}/dashboard"
                   style="background-color: #2563eb; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Go to Dashboard
                </a>
            </p>
        </body>
        </html>
        """

        try:
            resend.Emails.send({
                "from": from_address,
                "to": to_email,
                "subject": "Welcome to Social Card Service",
                "html": html
            })
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send welcome email: {e}")
            return False


# Singleton instance
email_service = EmailService()
