from datetime import datetime, timedelta, timezone
from typing import Optional, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User
from src.repository import users as repo_users
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
    if bearer_token:
        return bearer_token.credentials
    return oauth_token


async def get_email_from_token(token: str) -> str:
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
    token: str = Depends(get_token), db: AsyncSession = Depends(get_db)
) -> User:
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

    user = await repo_users.get_user_by_id(int(sub), db)
    if user is None:
        logger.warning(f"User with id={sub} not found")
        raise cred_exc
    return user


async def verify_refresh_token(refresh_token: str, db: AsyncSession) -> Optional[User]:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: Optional[str] = payload.get("sub")
        ttype: Optional[str] = payload.get("token_type")
        if sub is None or ttype != "refresh":
            return None
        user = await repo_users.get_user_by_id(int(sub), db)
        if not user or getattr(user, "refresh_token", None) != refresh_token:
            return None
        return user
    except JWTError as e:
        logger.error(f"Refresh token verification failed: {e}")
        return None
