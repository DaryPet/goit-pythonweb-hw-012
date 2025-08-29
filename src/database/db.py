import contextlib
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
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
        self._engine: AsyncEngine = create_async_engine(url, echo=False)
        self._session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    @contextlib.asynccontextmanager
    async def session(self):
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
