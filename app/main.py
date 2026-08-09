from fastapi import FastAPI
from sqlalchemy import text

from app.config.settings import get_settings
from app.database.database import engine


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    description="Conversational AI financial assistant",
    version=settings.app_version,
)


@app.get("/")
async def root() -> dict[str, str]:
    """Basic service information."""

    return {
        "status": "online",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic application health check."""

    return {
        "status": "healthy",
    }


@app.get("/ready")
async def readiness_check() -> dict[str, str]:
    """
    Check whether Atlas is ready to accept requests.

    The readiness check verifies that the application
    can communicate with the configured database.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "not_ready",
            "database": "unavailable",
        }