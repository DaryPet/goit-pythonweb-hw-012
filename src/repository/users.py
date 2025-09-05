from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas.users import UserCreate


async def create_user(body: UserCreate, password_hash: str, db: AsyncSession) -> User:
    """
    Creates a new user in the database.

    :param body: The registration data.
    :param password_hash: Hashed password (already подготовленный в сервисе).
    :param db: Database session.
    :return: The created user.
    """
    user = User(email=body.email, password_hash=password_hash)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    """
    Retrieves a user by email.
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(user_id: int, db: AsyncSession) -> Optional[User]:
    """
    Retrieves a user by ID.
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_refresh_token(
    user: User, refresh_token: str, db: AsyncSession
) -> None:
    """
    Updates refresh token for the user.
    """
    stmt = update(User).where(User.id == user.id).values(refresh_token=refresh_token)
    await db.execute(stmt)
    await db.commit()


async def update_avatar(user: User, avatar_url: str, db: AsyncSession) -> User:
    """
    Updates the avatar URL for the user.
    """
    user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(user)
    return user


async def verify_user(user: User, db: AsyncSession) -> User:
    """
    Marks the user as verified (after email confirmation).
    """
    user.is_verified = True
    await db.commit()
