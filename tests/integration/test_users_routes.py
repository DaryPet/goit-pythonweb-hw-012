import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status
from httpx import AsyncClient

from main import app
from src.database.models import User


class TestUsersRoutes:
    """A collection of refactored, clean, and behavior-preserving tests for user endpoints.

    Note: The test logic has not been changed—only refactored for readability and
    consistency (following the Arrange / Act / Assert pattern, using try/finally
    for cleanup, and using explicit fixtures and context managers).
    """

    @pytest.mark.asyncio
    async def test_read_users_me_returns_verified_user(
        self, client: AsyncClient, verified_user: User
    ):
        """Tests that GET /api/users/me returns a verified user with correct fields."""
        from src.api.users import get_current_user

        try:
            # Arrange
            app.dependency_overrides[get_current_user] = lambda: verified_user

            # Act
            response = await client.get("/api/users/me")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == verified_user.email
            assert data["is_verified"] is True
            assert "avatar_url" in data
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_read_users_me_returns_user_with_default_avatar(
        self, client: AsyncClient, session, mock_default_avatar
    ):
        """Tests that GET /api/users/me returns a default avatar URL if the user has none."""
        from src.api.users import get_current_user

        # Arrange: create a real user in the test DB without an avatar_url
        user = User(
            email="noavatar@example.com", password_hash="hash", is_verified=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        try:
            app.dependency_overrides[get_current_user] = lambda: user

            # Act
            response = await client.get("/api/users/me")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == user.email
            assert data["is_verified"] is True
            assert data["avatar_url"] == "http://test.url/default.png"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_read_users_me_returns_unverified_user(
        self, client: AsyncClient, unverified_user: User
    ):
        """Tests that GET /api/users/me returns an unverified user with is_verified=False."""
        from src.api.users import get_current_user

        try:
            app.dependency_overrides[get_current_user] = lambda: unverified_user

            # Act
            response = await client.get("/api/users/me")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == unverified_user.email
            assert data["is_verified"] is False
            assert "avatar_url" in data
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_read_users_me_handles_default_avatar_exception_gracefully(
        self, client: AsyncClient, session
    ):
        """Tests that GET /api/users/me doesn't fail if get_default_avatar raises an exception."""
        from src.api.users import get_current_user

        # Arrange: user without an avatar
        user = User(
            email="erroravatar@example.com", password_hash="hash", is_verified=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        try:
            app.dependency_overrides[get_current_user] = lambda: user

            # Patch get_default_avatar to raise an exception
            with patch(
                "src.api.users.get_default_avatar", new_callable=AsyncMock
            ) as mock_get_default:
                mock_get_default.side_effect = Exception("Error getting default avatar")

                # Act
                response = await client.get("/api/users/me")

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["email"] == user.email
                assert data["is_verified"] is True
                # The avatar_url should be present and safe (we only check for the key)
                assert "avatar_url" in data
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_update_avatar_success(
        self, client: AsyncClient, owner: User, mock_file, mock_repo_users: AsyncMock
    ):
        """Tests that PATCH /api/users/avatar successfully updates the user's avatar."""
        from src.api.users import get_current_user

        try:
            app.dependency_overrides[get_current_user] = lambda: owner

            with patch(
                "src.api.users.upload_avatar", new_callable=AsyncMock
            ) as mock_upload:
                mock_upload.return_value = "http://test.url/avatar.png"

                # Act
                response = await client.patch(
                    "/api/users/avatar",
                    files={"file": ("avatar.png", mock_file.file, "image/png")},
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["avatar_url"] == "http://test.url/avatar.png"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_update_avatar_raises_http_exception_on_failure(
        self, client: AsyncClient, owner: User, mock_file, mock_repo_users: AsyncMock
    ):
        """Tests that the endpoint returns a 500 HTTP status with a clear detail message on upload failure."""
        from src.api.users import get_current_user

        try:
            app.dependency_overrides[get_current_user] = lambda: owner

            with patch(
                "src.api.users.upload_avatar", new_callable=AsyncMock
            ) as mock_upload:
                mock_upload.side_effect = Exception("Error uploading file")

                # Act
                response = await client.patch(
                    "/api/users/avatar",
                    files={"file": ("avatar.png", mock_file.file, "image/png")},
                )

                # Assert
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                data = response.json()
                assert data["detail"] == "Failed to upload avatar. Please try again."
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_update_default_avatar_success(self, client: AsyncClient, mock_file):
        """Tests a successful update of the system default avatar by an admin."""
        from src.api.users import get_current_admin

        class Admin:
            id = 1
            role = "ADMIN"

        try:
            app.dependency_overrides[get_current_admin] = lambda: Admin()

            with patch(
                "src.api.users.upload_avatar", new_callable=AsyncMock
            ) as mock_upload:
                mock_upload.return_value = "http://test.url/default_admin.png"

                # Act
                response = await client.patch(
                    "/api/users/admin/default-avatar",
                    files={"file": ("default_avatar.png", mock_file.file, "image/png")},
                )

                # Assert
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["avatar_url"] == "http://test.url/default_admin.png"
                assert "message" in data
        finally:
            app.dependency_overrides.pop(get_current_admin, None)

    @pytest.mark.asyncio
    async def test_update_default_avatar_raises_http_exception_on_failure(
        self, client: AsyncClient, mock_file
    ):
        """Tests that a 500 is returned if upload_avatar fails when updating the system avatar."""
        from src.api.users import get_current_admin

        class Admin:
            id = 1
            role = "ADMIN"

        try:
            app.dependency_overrides[get_current_admin] = lambda: Admin()

            with patch(
                "src.api.users.upload_avatar", new_callable=AsyncMock
            ) as mock_upload:
                mock_upload.side_effect = Exception("Upload failed")

                # Act
                response = await client.patch(
                    "/api/users/admin/default-avatar",
                    files={"file": ("default_avatar.png", mock_file.file, "image/png")},
                )

                # Assert
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                data = response.json()
                assert data["detail"] == "Failed to update system default avatar"
        finally:
            app.dependency_overrides.pop(get_current_admin, None)
