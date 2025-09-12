import pytest
from unittest.mock import patch
from fastapi import HTTPException
from src.services import cloudinary_service


class TestUploadAvatar:
    """A collection of tests for the cloudinary_service.upload_avatar function."""

    @pytest.mark.asyncio
    async def test_success(self, mock_file):
        """Tests a successful avatar upload."""
        mock_result = {"secure_url": "http://test.url/avatar.png"}
        with patch(
            "cloudinary.uploader.upload", return_value=mock_result
        ) as mock_upload:
            url = await cloudinary_service.upload_avatar(mock_file, public_id="user_1")
        assert url == "http://test.url/avatar.png"
        mock_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_failure(self, mock_file):
        """Tests an error during avatar upload."""
        upload_patch = patch(
            "cloudinary.uploader.upload", side_effect=Exception("fail")
        )
        with upload_patch:
            with pytest.raises(HTTPException) as exc_info:
                await cloudinary_service.upload_avatar(mock_file, public_id="user_1")

        assert exc_info.value.status_code == 500
        assert "Failed to upload avatar" in exc_info.value.detail


class TestGetDefaultAvatar:
    """A collection of tests for the cloudinary_service.get_default_avatar function."""

    @pytest.mark.asyncio
    async def test_success(self):
        """Tests successful retrieval of the system default avatar."""
        build_url_patch = patch(
            "cloudinary.CloudinaryImage.build_url",
            return_value="http://test.url/default.png",
        )
        with build_url_patch:
            url = await cloudinary_service.get_default_avatar()
        assert url == "http://test.url/default.png"

    @pytest.mark.asyncio
    async def test_failure(self):
        """Tests an error when retrieving the system default avatar."""
        build_url_patch = patch(
            "cloudinary.CloudinaryImage.build_url", side_effect=Exception("fail")
        )

        with build_url_patch:
            with pytest.raises(HTTPException) as exc_info:
                await cloudinary_service.get_default_avatar()

        assert exc_info.value.status_code == 404
        assert "System default avatar not configured" in exc_info.value.detail
