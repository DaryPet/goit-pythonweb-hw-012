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
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created {token_type} token for sub={data.get('sub')}")
    return token


def create_access_token(sub: str | int, minutes: Optional[int] = None) -> str:
    exp = minutes if minutes is not None else ACCESS_TOKEN_EXPIRES_MIN
    return _create_token({"sub": str(sub)}, timedelta(minutes=exp), "access")


def create_refresh_token(sub: str | int, days: Optional[int] = None) -> str:
    exp_days = days if days is not None else REFRESH_TOKEN_EXPIRES_DAYS
    return _create_token({"sub": str(sub)}, timedelta(days=exp_days), "refresh")


def create_email_token(sub: str | int) -> str:
    return _create_token({"sub": str(sub)}, timedelta(days=1), "email_verification")
