from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.schemas.users import UserResponse
from src.services.auth import get_current_user
from src.database.models import User
from src.repository import users as repository_users
from src.services.cloudinary_service import upload_avatar
from src.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
    description="No more then 10 calls per minute",
)
async def read_users_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get info about current user.
    """
    return current_user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user's avatar.
    Upload file into Cloudinary and save URL.
    """
    try:
        avatar_url = await upload_avatar(file, public_id=f"user_{current_user.id}")
        updated_user = await repository_users.update_avatar(
            current_user, avatar_url, db
        )
        return updated_user
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar. Please try again.",
        )
