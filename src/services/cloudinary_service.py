import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, status

from src.conf.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


async def upload_avatar(file, public_id: str) -> str:
    """
    Uploads an image to Cloudinary and returns the URL.

    :param file: UploadFile object from FastAPI
    :param public_id: Unique public identifier for the image
    :return: Secure URL of the uploaded image
    :raises HTTPException: If upload fails
    """
    try:
        logger.info(f"Uploading avatar with public_id: {public_id}")
        result = cloudinary.uploader.upload(
            file.file,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
            folder="avatars",
        )
        avatar_url = result.get("secure_url")
        logger.info(f"Avatar uploaded successfully: {avatar_url}")
        return avatar_url

    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar to cloud service",
        )
