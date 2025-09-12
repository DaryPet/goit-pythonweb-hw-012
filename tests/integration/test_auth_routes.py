import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status
from httpx import AsyncClient

from src.database.models import User
from src.security.tokens import create_refresh_token


class TestAuthRoutes:
    """A collection of tests for authentication endpoints."""

    @pytest.mark.asyncio
    @patch("src.api.auth.send_verification_email", new_callable=AsyncMock)
    async def test_signup_user(
        self,
        mock_send_email: AsyncMock,
        client: AsyncClient,
        mock_repo_users: AsyncMock,
    ):
        """
        Tests successful user signup.
        """
        # Arrange
        mock_send_email.return_value = None
        user_mock = MagicMock()
        user_mock.id = 1
        user_mock.email = "newuser@example.com"
        user_mock.is_verified = False
        user_mock.role = "USER"
        user_mock.avatar_url = "https://example.com/default.png"
        user_mock.created_at = "2025-09-11T12:00:00Z"
        mock_repo_users.get_user_by_email.return_value = None
        mock_repo_users.create_user.return_value = user_mock

        # Act
        with patch(
            "src.api.auth.get_password_hash",
            new=MagicMock(return_value="fake_hashed_password"),
        ):
            response = await client.post(
                "/api/auth/signup",
                json={"email": "newuser@example.com", "password": "password123"},
            )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_signup_existing_user(
        self, client: AsyncClient, unverified_user: User, mock_repo_users: AsyncMock
    ):
        """
        Tests signup with an email that already exists.
        """
        # Arrange
        mock_repo_users.get_user_by_email.return_value = unverified_user

        # Act
        response = await client.post(
            "/api/auth/signup",
            json={"email": unverified_user.email, "password": "password123"},
        )

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == "User with this email already exists"

    @pytest.mark.asyncio
    async def test_login_user_success(
        self, client: AsyncClient, verified_user: User, mock_repo_users: AsyncMock
    ):
        """
        Tests successful login with a verified user.
        """
        # Arrange
        mock_repo_users.get_user_by_email.return_value = verified_user
        with patch("src.api.auth.verify_password", new=MagicMock(return_value=True)):
            # Act
            response = await client.post(
                "/api/auth/login",
                data={"username": verified_user.email, "password": "hashed_password"},
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        mock_repo_users.update_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_unverified_user(
        self, client: AsyncClient, unverified_user: User, mock_repo_users: AsyncMock
    ):
        """
        Tests that an unverified user cannot log in.
        """
        # Arrange
        mock_repo_users.get_user_by_email.return_value = unverified_user

        # Act
        with patch("src.api.auth.verify_password", new=MagicMock(return_value=True)):
            response = await client.post(
                "/api/auth/login",
                data={"username": unverified_user.email, "password": "hashed_password"},
            )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            response.json()["detail"]
            == "Your email is not verified. Please check your mailbox."
        )

    @pytest.mark.asyncio
    async def test_login_incorrect_password(
        self, client: AsyncClient, verified_user: User, mock_repo_users: AsyncMock
    ):
        """
        Tests login with an incorrect password.
        """
        # Arrange
        mock_repo_users.get_user_by_email.return_value = verified_user

        # Act
        with patch("src.api.auth.verify_password", new=MagicMock(return_value=False)):
            response = await client.post(
                "/api/auth/login",
                data={"username": verified_user.email, "password": "wrong_password"},
            )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect email or password"

    @pytest.mark.asyncio
    async def test_login_non_existent_user(
        self, client: AsyncClient, mock_repo_users: AsyncMock
    ):
        """
        Tests login with a non-existent user.
        """
        # Arrange
        mock_repo_users.get_user_by_email.return_value = None

        # Act
        response = await client.post(
            "/api/auth/login",
            data={"username": "non_existent@example.com", "password": "password123"},
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect email or password"

    @pytest.mark.asyncio
    @patch("src.api.auth.get_redis_client", new=MagicMock(return_value=MagicMock()))
    async def test_refresh_token_success(
        self, client: AsyncClient, verified_user: User, mock_repo_users: AsyncMock
    ):
        """
        Tests successful refresh of an access token.
        """
        # Arrange
        refresh_token = create_refresh_token(verified_user.id)
        verified_user.refresh_token = refresh_token

        # Act
        with patch(
            "src.api.auth.verify_refresh_token",
            new_callable=AsyncMock,
            return_value=verified_user,
        ):
            response = await client.post(
                "/api/auth/refresh_token",
                headers={"Authorization": f"Bearer {refresh_token}"},
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        mock_repo_users.update_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.api.auth.get_redis_client", new=MagicMock(return_value=MagicMock()))
    async def test_refresh_token_invalid_token(self, client: AsyncClient):
        """
        Tests a failed token refresh with an invalid token.
        """
        # Arrange & Act
        with patch(
            "src.api.auth.verify_refresh_token",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.post(
                "/api/auth/refresh_token",
                headers={"Authorization": "Bearer invalid_token"},
            )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid refresh token"

    @pytest.mark.asyncio
    async def test_confirmed_email_success(
        self, client: AsyncClient, unverified_user: User, mock_repo_users: AsyncMock
    ):
        """
        Tests successful email confirmation.
        """
        # Arrange
        mock_token = "some_signature_token"
        mock_repo_users.get_user_by_email.return_value = unverified_user

        # Act
        with patch(
            "src.api.auth.get_email_from_token",
            new_callable=AsyncMock,
            return_value=unverified_user.email,
        ):
            response = await client.get(f"/api/auth/confirmed_email/{mock_token}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Email successfully confirmed"
        mock_repo_users.verify_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirmed_email_already_confirmed(
        self, client: AsyncClient, verified_user: User, mock_repo_users: AsyncMock
    ):
        """
        Tests confirming an email that is already verified.
        """
        # Arrange
        mock_token = "some_signature_token"
        mock_repo_users.get_user_by_email.return_value = verified_user

        # Act
        with patch(
            "src.api.auth.get_email_from_token",
            new_callable=AsyncMock,
            return_value=verified_user.email,
        ):
            response = await client.get(f"/api/auth/confirmed_email/{mock_token}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Your email is already confirmed"

    @pytest.mark.asyncio
    async def test_confirmed_email_invalid_token(
        self, client: AsyncClient, mock_repo_users: AsyncMock
    ):
        """
        Tests an email confirmation with an invalid token.
        """
        # Arrange
        mock_repo_users.get_user_by_email.return_value = None

        # Act
        with patch(
            "src.api.auth.get_email_from_token",
            new_callable=AsyncMock,
            return_value="invalid_email@example.com",
        ):
            response = await client.get(
                "/api/auth/confirmed_email/some_valid_looking_token"
            )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Verification error"

    @pytest.mark.asyncio
    async def test_password_reset_request_success(
        self, client: AsyncClient, verified_user: User, mock_repo_users: AsyncMock
    ):
        """
        Tests a successful password reset request.
        """
        # Arrange
        mock_repo_users.get_user_by_email.return_value = verified_user

        # Act
        with patch(
            "src.api.auth.send_password_reset_email", new_callable=AsyncMock
        ) as mock_send_email:
            response = await client.post(
                "/api/auth/password-reset-request", json={"email": verified_user.email}
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert (
            response.json()["message"]
            == "If email exists, password reset instructions will be sent"
        )
        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_password_reset_confirm_success(
        self, client: AsyncClient, verified_user: User, mock_repo_users: AsyncMock
    ):
        """
        Tests a successful password reset confirmation and new password setting.
        """
        # Arrange
        mock_token = "some_reset_token"
        mock_repo_users.get_user_by_email.return_value = verified_user

        # Act
        with (
            patch(
                "src.api.auth.verify_password_reset_token",
                new_callable=AsyncMock,
                return_value=verified_user.email,
            ),
            patch(
                "src.api.auth.get_password_hash",
                new=MagicMock(return_value="new_hashed_password"),
            ),
        ):

            response = await client.post(
                "/api/auth/password-reset-confirm",
                json={"token": mock_token, "new_password": "new_password123"},
            )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Password successfully reset"

    @pytest.mark.asyncio
    async def test_password_reset_confirm_invalid_token(
        self, client: AsyncClient, mock_repo_users: AsyncMock
    ):
        """
        Tests a failed password reset confirmation with an invalid token.
        """
        # Arrange
        mock_repo_users.get_user_by_email.return_value = None

        # Act
        with patch(
            "src.api.auth.verify_password_reset_token",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.post(
                "/api/auth/password-reset-confirm",
                json={"token": "invalid_token", "new_password": "new_password123"},
            )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid reset token"
