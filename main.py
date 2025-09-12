"""
Main application entry point for the Contacts REST API.

This module sets up the FastAPI application, including middleware, routing,
and exception handling.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from redis.asyncio import from_url as redis_from_url
from sqlalchemy.exc import SQLAlchemyError

from src.api.contacts import router as contacts_router
from src.api.auth import router as auth_router
from src.api.users import router as users_router

from src.conf.config import settings
from src.core.logger import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.

    This context manager initializes and properly closes connections to external
    services like Redis for rate limiting.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Yields control back to the application to run.
    """
    redis = redis_from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis)
    try:

        yield
    finally:
        await redis.close()
        await redis.connection_pool.disconnect()


setup_logging()

app = FastAPI(
    title="Contacts REST API",
    version="1.0.0",
    description="API для зберігання та управління контактами (FastAPI + SQLAlchemy + PostgreSQL).",
    lifespan=lifespan,
)


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handles SQLAlchemy-related exceptions.

    Logs the database error and returns a generic 500 Internal Server Error
    response to the client to avoid exposing sensitive database details.

    Args:
        request (Request): The incoming request that caused the exception.
        exc (SQLAlchemyError): The SQLAlchemy exception instance.

    Returns:
        JSONResponse: A JSON response with an error message and status code 500.
    """
    logger.error(f"Database error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500, content={"detail": "Database operation failed"}
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(contacts_router, prefix="/api", tags=["contacts"])
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(users_router, prefix="/api", tags=["users"])


@app.get("/")
def health_check():
    """
    Checks the health of the API.

    This is a simple endpoint to verify that the application is running
    and responsive.

    Returns:
        dict: A dictionary with a status key set to "ok".
    """
    return {"status": "ok"}
