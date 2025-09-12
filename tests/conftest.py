import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.database.models import Base, User
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import AsyncClient
from main import app
import httpx
from main import app
from src.api.auth import get_db
from src.api.contacts import get_db as get_db_contacts
from fastapi_limiter import FastAPILimiter

TEST_DB_URL = "sqlite+aiosqlite:///./test_unit.db"
engine = create_async_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
def override_get_db():
    """
    Overrides the get_db dependency with a mock for all tests.
    """
    app.dependency_overrides[get_db] = lambda: MagicMock(spec=AsyncSession)
    app.dependency_overrides[get_db_contacts] = lambda: MagicMock(spec=AsyncSession)
    yield
    app.dependency_overrides.clear()



@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_db():
    """
    Initializes and cleans up the test database for each test function.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def session():
    """
    Provides an asynchronous test database session.
    """
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def redis_mock():
    """
    Mocks the Redis client for tests.
    """
    from unittest.mock import AsyncMock

    return AsyncMock()


@pytest_asyncio.fixture
async def owner(session):
    """
    Creates and returns a primary user for testing.
    """
    user = User(email="owner@example.com", password_hash="hashed_password", role="USER")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def another_owner(session):
    """
    Creates and returns a primary user for testing.
    """
    user = User(
        email="another_owner@example.com", password_hash="hashed_password", role="USER"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
def mock_file():
    """
    Provides a mock file for upload tests.
    """
    file_mock = MagicMock()
    file_mock.file = b"dummy data"
    return file_mock


@pytest_asyncio.fixture
def cloudinary_build_url_mock():
    """
    Mocks Cloudinary's build_url function.
    """
    with patch(
        "cloudinary.CloudinaryImage.build_url",
        return_value="http://test.url/default.png",
    ) as mock:
        yield mock


@pytest_asyncio.fixture
async def verified_user(session):
    """
    Creates and returns a verified user for tests.
    """
    user = User(
        email="verified@example.com",
        password_hash="$2b$12$hashed_password",
        is_verified=True,
        role="USER",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def unverified_user(session):
    """
    Creates and returns an unverified user for tests.
    """
    user = User(
        email="unverified@example.com",
        password_hash="$2b$12$hashed_password",
        is_verified=False,
        role="USER",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def client():
    """
    Provides an asynchronous HTTP client for testing FastAPI endpoints.
    """
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def mock_repo_users():
    """
    Mocks the user repository and patches it in the auth API module.
    """
    repo_mock = AsyncMock()
    with patch("src.api.auth.repository_users", new=repo_mock) as _mock:
        yield repo_mock


@pytest_asyncio.fixture
async def mock_repo_contacts():
    """
    Mocks the contact repository and patches it in the contacts API module.
    """

    repo_mock = AsyncMock()

    with patch("src.api.contacts.repository_contacts", new=repo_mock) as _mock:

        yield repo_mock


@pytest_asyncio.fixture(autouse=True)
async def override_get_current_user():
    """
    Automatically overrides the get_current_user dependency for contacts tests.
    """
    from src.api.contacts import get_current_user as original_get_current_user
    from src.database.models import User
    async def mock_get_current_user():
        return User(id=1, email="test@example.com", role="USER")

    app.dependency_overrides[original_get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(original_get_current_user, None)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def mock_fastapi_limiter():
    """
    Mocks the FastAPILimiter to bypass Redis dependencies for tests.
    """
    with patch.object(FastAPILimiter, "init", new_callable=AsyncMock):
        FastAPILimiter.redis = AsyncMock()
        FastAPILimiter.identifier = AsyncMock(return_value="test_key")
        FastAPILimiter.http_callback = AsyncMock()
        yield
        FastAPILimiter.redis = None
        FastAPILimiter.identifier = None
        FastAPILimiter.http_callback = None

@pytest_asyncio.fixture
def mock_default_avatar():
    """
    Mocks the get_default_avatar function to return a test URL.
    """
    with patch("src.api.users.get_default_avatar", new_callable=AsyncMock) as mock:
        mock.return_value = "http://test.url/default.png"
        yield mock


@pytest_asyncio.fixture
def mock_upload_avatar():
    """
    Mocks the upload_avatar function to return a test URL.
    """
    with patch(
        "src.services.cloudinary_service.upload_avatar", new_callable=AsyncMock
    ) as mock:
        mock.return_value = "http://test.url/avatar.png"
        yield mock
