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
    """Send verification email to user"""
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