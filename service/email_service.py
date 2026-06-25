"""Email notification service for the application.

This module provides functions for sending transactional emails
such as email verification and password reset links using FastAPI-Mail.
"""

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

from db import settings


conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_verification_email(email: EmailStr, verification_token: str, host: str = 'localhost:8000'):
    """Send an email verification link to a newly registered user.

    Constructs a verification URL and sends an HTML email with a
    clickable link to confirm the user's email address.

    Args:
        email: The recipient's email address.
        verification_token: The unique verification token to include in the URL.
        host: The hostname for the verification URL (default: localhost:8000).
    """
    verification_url = f'http://{host}/api/auth/confirm_email/{verification_token}'

    message = MessageSchema(
        subject='Email Verification',
        recipients=[email],
        body=f"""
        <h2>Email Verification</h2>
        <p>Thank you for registering! Please verify your email by clicking the link below:</p>
        <p><a href="{verification_url}">Verify Email</a></p>
        <p>Or copy and paste this URL in your browser:</p>
        <p>{verification_url}</p>
        <p>If you did not register, please ignore this email.</p>
        """,
        subtype='html',
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_reset_password_email(email: EmailStr, reset_token: str, host: str = 'localhost:8000'):
    """Send a password reset link to a user.

    Constructs a reset URL with the token and sends an HTML email
    with instructions to reset the user's password.

    Args:
        email: The recipient's email address.
        reset_token: The unique password reset token.
        host: The hostname for the reset URL (default: localhost:8000).
    """
    reset_url = f'http://{host}/api/auth/password-reset/confirm?token={reset_token}'

    message = MessageSchema(
        subject='Password Reset',
        recipients=[email],
        body=f"""
        <h2>Password Reset</h2>
        <p>You have requested a password reset. Click the link below to reset your password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>Or copy and paste this URL in your browser:</p>
        <p>{reset_url}</p>
        <p>This link will expire in 15 minutes.</p>
        <p>If you did not request a password reset, please ignore this email.</p>
        """,
        subtype='html',
    )

    fm = FastMail(conf)
    await fm.send_message(message)