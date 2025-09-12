import contextlib
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import SQLAlchemyError
from src.conf.config import settings


class DatabaseSessionManager:
    """
    Manages asynchronous database sessions for SQLAlchemy.

    This class handles the creation of the async engine and provides a context manager
    for managing database sessions, ensuring transactions are properly committed or
    rolled back.
    """

    def __init__(self, url: str):
        """
        Initializes the DatabaseSessionManager with a database URL.

        Args:
            url (str): The database connection string.
        """
        self._engine: AsyncEngine = create_async_engine(
            url,
            echo=True,
            connect_args={"server_settings": {"client_encoding": "utf8"}},
        )
        self._session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Provides a managed asynchronous database session.

        This context manager handles the session lifecycle, including
        committing changes on success and rolling back on errors.

        Yields:
            AsyncSession: The asynchronous database session.
        """
        session = self._session_maker()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    FastAPI dependency that provides a managed database session.

    This function is used in API endpoints to inject a database session,
    ensuring that a new session is created for each request.

    Yields:
        AsyncSession: The asynchronous database session.
    """
    async with sessionmanager.session() as session:
        yield session
