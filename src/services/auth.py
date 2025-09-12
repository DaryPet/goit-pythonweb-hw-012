from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User, UserRole
from src.repository import users as repo_users
from src.services.redis_service import get_redis_client
from src.core.logger import get_logger

logger = get_logger(__name__)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

http_bearer = HTTPBearer(auto_error=False)


async def get_token(
    oauth_token: str = Depends(oauth2_scheme),
    bearer_token: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> str:
    """
    Retrieves the authentication token from either OAuth2 or HTTP Bearer schemes.

    This function serves as a dependency to handle tokens provided in different
    ways in the Authorization header.

    Args:
        oauth_token (str, optional): Token from the OAuth2PasswordBearer scheme. Defaults to Depends(oauth2_scheme).
        bearer_token (HTTPAuthorizationCredentials, optional): Token from the HTTPBearer scheme. Defaults to Depends(http_bearer).

    Returns:
        str: The raw token string.
    """
    if bearer_token:
        return bearer_token.credentials
    return oauth_token


async def get_email_from_token(token: str) -> str:
    """
    Decodes an email verification token and extracts the user's email address.

    Args:
        token (str): The JWT token for email verification.

    Raises:
        HTTPException: If the token is invalid or its purpose is not email verification.

    Returns:
        str: The user's email address.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("token_type") != "email_verification":
            raise JWTError("Invalid token scope")
        email = payload.get("sub")
        if email is None:
            raise JWTError("Missing subject in token")
        return email
    except JWTError as e:
        logger.error(f"Email token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token for email verification",
        )


async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> User:
    """
    Retrieves the current authenticated user from an access token.

    This function acts as a dependency that validates the access token,
    checks if the user exists in the database, and returns the user object.

    Args:
        token (str, optional): The access token. Defaults to Depends(get_token).
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        redis (Redis, optional): The Redis client. Defaults to Depends(get_redis_client).

    Raises:
        HTTPException: If the credentials cannot be validated or the user is not found.

    Returns:
        User: The authenticated user object.
    """
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: Optional[str] = payload.get("sub")
        ttype: Optional[str] = payload.get("token_type")
        if sub is None or ttype != "access":
            raise cred_exc
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise cred_exc

    user = await repo_users.get_user_by_id(int(sub), db, redis)
    if user is None:
        logger.warning(f"User with id={sub} not found")
        raise cred_exc
    return user


async def verify_refresh_token(
    refresh_token: str, db: AsyncSession, redis: Redis
) -> Optional[User]:
    """
    Verifies a refresh token and returns the corresponding user.

    This function validates the token's signature, checks if it's a refresh token,
    and ensures it matches the token stored in the database for the user.

    Args:
        refresh_token (str): The refresh token to verify.
        db (AsyncSession): The database session.
        redis (Redis): The Redis client instance.

    Returns:
        Optional[User]: The user object if the token is valid, otherwise None.
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: Optional[str] = payload.get("sub")
        ttype: Optional[str] = payload.get("token_type")
        if sub is None or ttype != "refresh":
            return None
        user = await repo_users.get_user_by_id(int(sub), db, redis)
        if not user or getattr(user, "refresh_token", None) != refresh_token:
            return None
        return user
    except JWTError as e:
        logger.error(f"Refresh token verification failed: {e}")
        return None


async def get_current_admin(current_user: User = Depends(get_current_user)):
    """
    Verify that current user has admin role.

    This function acts as a dependency to ensure only administrators can access
    a specific endpoint.

    Args:
        current_user (User): The authenticated user from the get_current_user dependency.

    Raises:
        HTTPException: If the user does not have the ADMIN role.

    Returns:
        User: The user object if they are an administrator.
    """
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.id} attempted admin action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action",
        )
    return current_user


async def verify_password_reset_token(token: str) -> str:
    """
    Verifies a password reset token and returns the user's email.

    Args:
        token (str): The password reset token.

    Raises:
        HTTPException: If the token is invalid or expired.

    Returns:
        str: The email address associated with the token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("token_type") != "password_reset":
            raise JWTError("Invalid token scope")
        email = payload.get("sub")
        if email is None:
            raise JWTError("Missing subject in token")
        return email
    except JWTError as e:
        logger.error(f"Password reset token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid password reset token",
        )
