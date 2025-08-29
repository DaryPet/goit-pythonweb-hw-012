from src.api.contacts import router as contacts_router
from fastapi import FastAPI
from src.core.logger import setup_logging

setup_logging()

app = FastAPI(
    title="Contacts REST API",
    version="1.0.0",
    description="API для зберігання та управління контактами (FastAPI + SQLAlchemy + PostgreSQL).",
)

app.include_router(contacts_router, prefix="/api", tags=["contacts"])

@app.get("/")
def health_check():
    return {"status": "ok"}
