from datetime import datetime, timedelta, timezone
from typing import Optional, Literal
from jose import jwt
from src.conf.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRES_MIN = int(settings.ACCESS_TOKEN_EXPIRES_MIN)
REFRESH_TOKEN_EXPIRES_DAYS = int(settings.REFRESH_TOKEN_EXPIRES_DAYS)


def _create_token(
    data: dict,
    expires_delta: timedelta,
    token_type: Literal["access", "refresh", "email_verification"],
) -> str:
    """
    Creates a JWT token with specified data and expiration time.

    This is a helper function that handles the core token creation logic.
    It adds 'exp', 'iat', and 'token_type' claims to the token payload.

    Args:
        data (dict): The payload to be encoded in the token.
        expires_delta (timedelta): The timedelta for the token's expiration.
        token_type (Literal["access", "refresh", "email_verification"]): The type of the token.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created {token_type} token for sub={data.get('sub')}")
    return token


def create_access_token(sub: str | int, minutes: Optional[int] = None) -> str:
    """
    Creates a new access token.

    Args:
        sub (str | int): The subject of the token, typically a user's ID.
        minutes (Optional[int], optional): The token's expiration time in minutes. Defaults to ACCESS_TOKEN_EXPIRES_MIN.

    Returns:
        str: The encoded access token.
    """
    exp = minutes if minutes is not None else ACCESS_TOKEN_EXPIRES_MIN
    return _create_token({"sub": str(sub)}, timedelta(minutes=exp), "access")


def create_refresh_token(sub: str | int, days: Optional[int] = None) -> str:
    """
    Creates a new refresh token.

    Args:
        sub (str | int): The subject of the token, typically a user's ID.
        days (Optional[int], optional): The token's expiration time in days. Defaults to REFRESH_TOKEN_EXPIRES_DAYS.

    Returns:
        str: The encoded refresh token.
    """
    exp_days = days if days is not None else REFRESH_TOKEN_EXPIRES_DAYS
    return _create_token({"sub": str(sub)}, timedelta(days=exp_days), "refresh")


def create_email_token(sub: str | int) -> str:
    """
    Creates a new email verification token.

    Args:
        sub (str | int): The subject of the token, typically a user's ID.

    Returns:
        str: The encoded email verification token.
    """
    return _create_token({"sub": str(sub)}, timedelta(days=1), "email_verification")


def create_password_reset_token(sub: str | int) -> str:
    """
    Creates a token for password reset.
    Expires in 1 hour for security.

    Args:
        sub (str | int): The subject of the token, typically a user's email.

    Returns:
        str: The encoded password reset token.
    """
    return _create_token({"sub": str(sub)}, timedelta(hours=1), "password_reset")
