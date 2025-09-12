import pytest
from jose import jwt
from fastapi import HTTPException
from unittest.mock import AsyncMock
from fastapi.security import HTTPAuthorizationCredentials

from src.services.auth import (
    get_email_from_token,
    verify_password_reset_token,
    get_token,
    get_current_user,
    get_current_admin,
    verify_refresh_token,
    SECRET_KEY,
    ALGORITHM,
)
from src.database.models import User, UserRole


class TestGetEmailFromToken:
    """Tests for the get_email_from_token function."""

    @pytest.mark.asyncio
    async def test_success(self):
        """
        Tests successful email extraction from a valid token.
        """
        token = jwt.encode(
            {"sub": "test@example.com", "token_type": "email_verification"},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        email = await get_email_from_token(token)
        assert email == "test@example.com"

    @pytest.mark.asyncio
    async def test_invalid_type(self):
        """
        Tests that an HTTPException is raised for a token with an invalid type.
        """
        token = jwt.encode(
            {"sub": "test@example.com", "token_type": "wrong_type"},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException):
            await get_email_from_token(token)


class TestVerifyPasswordResetToken:
    """Tests for the verify_password_reset_token function."""

    @pytest.mark.asyncio
    async def test_success(self):
        """
        Tests successful password reset token verification.
        """
        token = jwt.encode(
            {"sub": "reset@example.com", "token_type": "password_reset"},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        email = await verify_password_reset_token(token)
        assert email == "reset@example.com"

    @pytest.mark.asyncio
    async def test_invalid_type(self):
        """
        Tests that an HTTPException is raised for an invalid token type.
        """
        token = jwt.encode(
            {"sub": "reset@example.com", "token_type": "wrong_type"},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException):
            await verify_password_reset_token(token)


class TestGetToken:
    """Tests for the get_token utility function."""

    @pytest.mark.asyncio
    async def test_prefers_bearer(self):
        """
        Tests that the function prioritizes the Bearer token.
        """
        creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="bearer_token"
        )
        token = await get_token(bearer_token=creds, oauth_token="oauth_token")
        assert token == "bearer_token"

    @pytest.mark.asyncio
    async def test_fallback_to_oauth(self):
        """
        Tests that the function falls back to the OAuth2 token when no Bearer token is provided.
        """
        token = await get_token(bearer_token=None, oauth_token="oauth_token")
        assert token == "oauth_token"


class TestGetCurrentUser:
    """Tests for the get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_success(self, owner, session, redis_mock):
        """
        Tests successful retrieval of the current user.
        """
        token = jwt.encode(
            {"sub": str(owner.id), "token_type": "access"},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        redis_mock.get.return_value = None

        user = await get_current_user(token=token, db=session, redis=redis_mock)
        assert user.id == owner.id

    @pytest.mark.asyncio
    async def test_invalid_token(self, session, redis_mock):
        """
        Tests that an HTTPException is raised for an invalid token.
        """
        token = jwt.encode(
            {"sub": "1", "token_type": "wrong"}, SECRET_KEY, algorithm=ALGORITHM
        )
        redis_mock.get.return_value = None

        with pytest.raises(HTTPException):
            await get_current_user(token=token, db=session, redis=redis_mock)


class TestVerifyRefreshToken:
    """Tests for the verify_refresh_token function."""

    @pytest.mark.asyncio
    async def test_success(self, owner, session, redis_mock):
        """
        Tests successful verification of a refresh token.
        """
        token_str = jwt.encode(
            {"sub": str(owner.id), "token_type": "refresh"},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        owner.refresh_token = token_str
        session.add(owner)
        await session.commit()
        redis_mock.get.return_value = None

        user = await verify_refresh_token(token_str, db=session, redis=redis_mock)
        assert user.id == owner.id

    @pytest.mark.asyncio
    async def test_invalid(self, owner, session, redis_mock):
        """
        Tests that the function returns None for an invalid refresh token.
        """
        token_str = jwt.encode(
            {"sub": str(owner.id), "token_type": "refresh"},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        redis_mock.get.return_value = None

        user = await verify_refresh_token(token_str, db=session, redis=redis_mock)
        assert user is None


class TestGetCurrentAdmin:
    """Tests for the get_current_admin dependency."""

    @pytest.mark.asyncio
    async def test_success(self, owner):
        """
        Tests successful retrieval of an admin user.
        """
        fake_user = User(id=owner.id, role=UserRole.ADMIN)
        admin = await get_current_admin(current_user=fake_user)
        assert admin.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_forbidden(self, owner):
        """
        Tests that an HTTPException is raised when a non-admin user tries to access an admin endpoint.
        """
        fake_user = User(id=owner.id, role=UserRole.USER)
        with pytest.raises(HTTPException):
            await get_current_admin(current_user=fake_user)
