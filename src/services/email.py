from pathlib import Path
from fastapi import HTTPException, status

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

from src.conf.config import settings
from src.security.tokens import create_email_token
from src.core.logger import get_logger

logger = get_logger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_verification_email(email: EmailStr, username: str, host: str):
    """
    Sends an email with a verification token for user account activation.

    Args:
        email (EmailStr): The recipient's email address.
        username (str): The user's username for the email template.
        host (str): The application's host URL to create the verification link.

    Raises:
        HTTPException: If an error occurs while sending the email.
    """
    try:
        logger.info(f"⏳ Attempting to send email to: {email}")
        token_verification = create_email_token(email)
        logger.info(f"✅ Token created: {token_verification}")

        message = MessageSchema(
            subject="Verifying your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
        logger.info(f"📨 Email sent successfully to: {email}")
    except Exception as e:
        logger.error(f"Error during email validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again.",
        )


async def send_password_reset_email(
    email: EmailStr, username: str, host: str, reset_token: str
):
    """
    Sends a password reset email to a user.

    This function sends an email with a unique password reset token, allowing the
    user to securely change their password.

    Args:
        email (EmailStr): The recipient's email address.
        username (str): The user's username for the email template.
        host (str): The application's host URL to create the reset link.
        reset_token (str): The password reset token.

    Raises:
        HTTPException: If an error occurs while sending the email.
    """
    try:
        logger.info(f"⏳ Attempting to send password reset email to: {email}")

        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": reset_token,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="password_reset.html")
        logger.info(f"📨 Password reset email sent successfully to: {email}")
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email. Please try again.",
        )
