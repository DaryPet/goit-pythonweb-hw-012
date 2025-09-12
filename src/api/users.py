from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.schemas.users import UserResponse
from src.services.auth import get_current_user, get_current_admin
from src.database.models import User
from src.repository import users as repository_users
from src.services.cloudinary_service import upload_avatar, get_default_avatar
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
    Retrieves information about the currently authenticated user.

    If the user does not have a custom avatar, a default one is provided.

    Args:
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Returns:
        UserResponse: The user's information, including a verified status and avatar URL.
    """
    if not current_user.avatar_url:
        try:
            user_data = current_user.__dict__.copy()
            user_data["avatar_url"] = await get_default_avatar()
            return UserResponse(**user_data)
        except Exception:
            pass
    return current_user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates the authenticated user's avatar.

    The new avatar image is uploaded to Cloudinary, and its URL is saved
    in the database for the current user.

    Args:
        file (UploadFile, optional): The image file to upload. Defaults to File(...).
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the avatar upload fails.

    Returns:
        UserResponse: The updated user object with the new avatar URL.
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


@router.patch("/admin/default-avatar", response_model=dict)
async def update_default_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
):
    """
    Updates the system-wide default avatar.

    This endpoint is restricted to administrators and allows them to change the
    default avatar shown to all users who have not set a custom one.

    Args:
        file (UploadFile, optional): The image file to use as the new default avatar. Defaults to File(...).
        current_user (User, optional): The authenticated administrator. Defaults to Depends(get_current_admin).

    Raises:
        HTTPException: If the avatar upload fails.

    Returns:
        dict: A success message and the URL of the new default avatar.
    """
    try:
        avatar_url = await upload_avatar(file, public_id="system_default_avatar")
        logger.info(
            f"Admin {current_user.id} updated system default avatar to: {avatar_url}"
        )

        return {
            "message": "System default avatar updated successfully",
            "avatar_url": avatar_url,
        }
    except Exception as e:
        logger.error(f"Error updating default avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update system default avatar",
        )
