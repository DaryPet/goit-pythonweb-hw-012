from typing import Optional
import pickle

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.conf.config import settings
from redis.asyncio import Redis

from src.database.models import User
from src.schemas.users import UserCreate


async def create_user(body: UserCreate, password_hash: str, db: AsyncSession) -> User:
    """
    Creates a new user in the database.

    Args:
        body (UserCreate): The user's registration data.
        password_hash (str): The pre-hashed password.
        db (AsyncSession): The database session.

    Returns:
        User: The created user object.
    """
    user = User(email=body.email, password_hash=password_hash, role=body.role)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    """
    Retrieves a user by their email address.

    Args:
        email (str): The email of the user to retrieve.
        db (AsyncSession): The database session.

    Returns:
        Optional[User]: The user object if found, otherwise None.
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(
    user_id: int, db: AsyncSession, redis: Redis
) -> Optional[User]:
    """
    Retrieves a user by their ID, with Redis caching.

    First checks the Redis cache, and if the user is not found,
    fetches them from the database and stores the result in Redis.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (AsyncSession): The database session.
        redis (Redis): The Redis client instance.

    Returns:
        Optional[User]: The user object if found, otherwise None.
    """
    cache_key = f"user:{user_id}"
    cache_user = await redis.get(cache_key)

    if cache_user:
        return pickle.loads(cache_user)

    user = await db.scalar(select(User).where(User.id == user_id))

    if user:
        await redis.set(cache_key, pickle.dumps(user), ex=settings.REDIS_EXPIRES)
    return user


async def update_refresh_token(
    user: User, refresh_token: str, db: AsyncSession
) -> None:
    """
    Updates the refresh token for a user in the database.

    Args:
        user (User): The user whose refresh token needs to be updated.
        refresh_token (str): The new refresh token.
        db (AsyncSession): The database session.
    """
    stmt = update(User).where(User.id == user.id).values(refresh_token=refresh_token)
    await db.execute(stmt)
    await db.commit()


async def update_avatar(user: User, avatar_url: str, db: AsyncSession) -> User:
    """
    Updates the avatar URL for a user.

    Args:
        user (User): The user whose avatar needs to be updated.
        avatar_url (str): The new URL for the user's avatar.
        db (AsyncSession): The database session.

    Returns:
        User: The updated user object.
    """
    user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(user)
    return user


async def verify_user(user: User, db: AsyncSession) -> User:
    """
    Marks a user's account as verified.

    This function is typically called after a user confirms their email address.

    Args:
        user (User): The user object to be verified.
        db (AsyncSession): The database session.

    Returns:
        User: The verified user object.

    Raises:
        SQLAlchemyError: If a database operation fails.
    """
    if user and user in db:
        user.is_verified = True
        await db.commit()
        await db.refresh(user)
    return user
