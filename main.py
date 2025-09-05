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
    return {"status": "ok"}
