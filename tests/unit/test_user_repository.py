import pytest
import pickle
from unittest.mock import AsyncMock
from sqlalchemy.exc import IntegrityError
from src.repository.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_refresh_token,
    update_avatar,
    verify_user,
)
from src.schemas.users import UserCreate
from src.database.models import User, UserRole


class TestCreateUser:
    """A collection of tests for the create_user function."""

    @pytest.mark.asyncio
    async def test_user_creation(self, session):
        """Tests the creation of a regular user."""
        user_data = UserCreate(
            email="test@example.com", password="password123", role=UserRole.USER
        )
        user = await create_user(user_data, "hashed_password", session)
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.role == UserRole.USER
        assert user.id is not None

    @pytest.mark.asyncio
    async def test_create_user_with_admin_role(self, session):
        """Tests the creation of a user with an admin role."""
        user_data = UserCreate(
            email="admin@example.com", password="password123", role=UserRole.ADMIN
        )
        user = await create_user(user_data, "hashed_password", session)
        assert user.email == "admin@example.com"
        assert user.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_multiple_users_creation(self, session):
        """Tests the creation of multiple users and email lookup."""
        users_data = [
            UserCreate(
                email="user1@example.com", password="password123", role=UserRole.USER
            ),
            UserCreate(
                email="user2@example.com", password="password456", role=UserRole.USER
            ),
            UserCreate(
                email="admin@example.com", password="password789", role=UserRole.ADMIN
            ),
        ]
        created_users = []
        for user_data in users_data:
            user = await create_user(user_data, "hashed_password", session)
            created_users.append(user)
        await session.commit()
        assert len(created_users) == 3
        for i, user_data in enumerate(users_data):
            found_user = await get_user_by_email(user_data.email, session)
            assert found_user is not None
            assert found_user.email == user_data.email
            assert found_user.role.value == user_data.role.value

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, session):
        """Tests attempting to create a user with an existing email."""
        user_data = UserCreate(
            email="duplicate@example.com", password="password123", role=UserRole.USER
        )
        await create_user(user_data, "hashed_password", session)
        await session.commit()
        duplicate_user_data = UserCreate(
            email="duplicate@example.com", password="password456", role=UserRole.USER
        )
        with pytest.raises(IntegrityError):
            await create_user(duplicate_user_data, "hashed_password_2", session)


class TestGetUserByEmail:
    """A collection of tests for the get_user_by_email function."""

    @pytest.mark.asyncio
    async def test_found(self, session):
        """Tests that a user is successfully found by email."""
        user_data = UserCreate(
            email="test@example.com", password="password123", role=UserRole.USER
        )
        created_user = await create_user(user_data, "hashed_password", session)
        await session.commit()
        user = await get_user_by_email("test@example.com", session)
        assert user is not None
        assert user.email == "test@example.com"
        assert user.id == created_user.id

    @pytest.mark.asyncio
    async def test_not_found(self, session):
        """Tests that no user is returned for a non-existent email."""
        user = await get_user_by_email("nonexistent@example.com", session)
        assert user is None


class TestGetUserById:
    """A collection of tests for the get_user_by_id function."""

    @pytest.mark.asyncio
    async def test_from_cache(self):
        """Tests that a user is retrieved from the Redis cache."""
        redis_mock = AsyncMock()
        session_mock = AsyncMock()
        test_user = User(
            id=1,
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.USER,
        )
        redis_mock.get.return_value = pickle.dumps(test_user)
        user = await get_user_by_id(1, session_mock, redis_mock)
        assert user is not None
        assert user.id == 1
        assert user.email == "test@example.com"
        redis_mock.get.assert_called_once_with("user:1")
        session_mock.scalar.assert_not_called()

    @pytest.mark.asyncio
    async def test_from_db(self):
        """Tests that a user is retrieved from the database when not in cache."""
        redis_mock = AsyncMock()
        session_mock = AsyncMock()
        test_user = User(
            id=1,
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.USER,
        )
        redis_mock.get.return_value = None
        session_mock.scalar.return_value = test_user
        redis_mock.set.return_value = None
        user = await get_user_by_id(1, session_mock, redis_mock)
        assert user is not None
        assert user.id == 1
        assert user.email == "test@example.com"
        redis_mock.get.assert_called_once_with("user:1")
        session_mock.scalar.assert_called_once()
        redis_mock.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_not_found(self):
        """Tests that no user is returned when not found in cache or database."""
        redis_mock = AsyncMock()
        session_mock = AsyncMock()
        redis_mock.get.return_value = None
        session_mock.scalar.return_value = None
        user = await get_user_by_id(999, session_mock, redis_mock)
        assert user is None
        redis_mock.get.assert_called_once_with("user:999")
        session_mock.scalar.assert_called_once()
        redis_mock.set.assert_not_called()


class TestUpdateUser:
    """A collection of tests for user update functions."""

    @pytest.mark.asyncio
    async def test_update_refresh_token(self, session):
        """Tests updating a user's refresh token."""
        user_data = UserCreate(
            email="test@example.com", password="password123", role=UserRole.USER
        )
        user = await create_user(user_data, "hashed_password", session)
        await session.commit()
        new_token = "new_refresh_token"
        await update_refresh_token(user, new_token, session)
        await session.refresh(user)
        assert user.refresh_token == new_token

    @pytest.mark.asyncio
    async def test_update_refresh_token_non_existent_user(self, session):
        """Tests updating the refresh token for a non-existent user."""
        non_existent_user = User(
            id=999,
            email="nonexistent@example.com",
            password_hash="fake_hash",
            role=UserRole.USER,
        )
        new_token = "another_token"
        await update_refresh_token(non_existent_user, new_token, session)

    @pytest.mark.asyncio
    async def test_update_avatar(self, session):
        """Tests updating a user's avatar."""
        user_data = UserCreate(
            email="test@example.com", password="password123", role=UserRole.USER
        )
        user = await create_user(user_data, "hashed_password", session)
        await session.commit()
        avatar_url = "https://example.com/avatar.jpg"
        updated_user = await update_avatar(user, avatar_url, session)
        assert updated_user.avatar_url == avatar_url
        assert updated_user.id == user.id


class TestVerifyUser:
    """A collection of tests for the verify_user function."""

    @pytest.mark.asyncio
    async def test_verification(self, session):
        """Tests a user's successful verification."""
        user_data = UserCreate(
            email="test@example.com", password="password123", role=UserRole.USER
        )
        user = await create_user(user_data, "hashed_password", session)
        await session.commit()
        assert user.is_verified is False
        await verify_user(user, session)
        await session.refresh(user)
        assert user.is_verified is True

    @pytest.mark.asyncio
    async def test_verify_already_verified_user(self, session):
        """Tests re-verification of an already verified user."""
        user_data = UserCreate(
            email="verified@example.com", password="password123", role=UserRole.USER
        )
        user = await create_user(user_data, "hashed_password", session)
        user.is_verified = True
        await session.commit()
        await session.refresh(user)
        await verify_user(user, session)
        await session.refresh(user)
        assert user.is_verified is True

    @pytest.mark.asyncio
    async def test_verify_non_existent_user_no_exception(self, session):
        """Tests that verifying a non-existent user does not raise an exception."""
        non_existent_user = User(
            id=999,
            email="nonexistent@example.com",
            password_hash="fake_hash",
            role=UserRole.USER,
        )
        try:
            await verify_user(non_existent_user, session)
            assert True
        except Exception as e:
            pytest.fail(f"The function unexpectedly raised an exception: {e}")
