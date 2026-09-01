"""
SOC Dashboard backend — FastAPI entrypoint.

Connects to Wazuh SIEM (Mock or Real) and manages overlay state in PostgreSQL.
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import agents_router, alerts_router, cases_router, stats_router

logger = logging.getLogger("uvicorn.error")


def check_postgres_health() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.warning(f"Postgres health check failed: {e}")
        return False


def check_redis_health() -> bool:
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        return bool(r.ping())
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify database connection on startup
    logger.info("Initializing SOC Dashboard backend...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully.")
    except Exception as e:
        logger.critical(f"FATAL: Database connection failed on startup: {e}")
        raise RuntimeError(f"Database connection failed on startup: {e}") from e

    logger.info(f"Wazuh mode: {settings.WAZUH_MODE.upper()}")
    yield
    logger.info("Shutting down SOC Dashboard backend...")


app = FastAPI(
    title="SOC Dashboard API",
    version="0.2.0",
    description="FastAPI service for SOC alert triage, case management, and Wazuh SIEM telemetry.",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    postgres_reachable: bool
    redis_reachable: bool
    wazuh_configured: bool
    # Backwards-compatibility aliases for frontend placeholder
    postgres_configured: bool = True
    redis_configured: bool = True


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness/readiness probe performing live connection checks to Postgres and Redis."""
    pg_ok = check_postgres_health()
    redis_ok = check_redis_health()
    wazuh_ok = bool(settings.WAZUH_API_URL)

    overall_status = "ok" if (pg_ok and redis_ok) else "degraded"

    return HealthResponse(
        status=overall_status,
        postgres_reachable=pg_ok,
        redis_reachable=redis_ok,
        wazuh_configured=wazuh_ok,
        postgres_configured=pg_ok,
        redis_configured=redis_ok,
    )


@app.get("/")
def root() -> dict:
    return {
        "service": "soc-dashboard-backend",
        "version": "0.2.0",
        "wazuh_mode": settings.WAZUH_MODE,
        "docs": "/docs",
    }


# Include Routers
app.include_router(alerts_router)
app.include_router(agents_router)
app.include_router(stats_router)
app.include_router(cases_router)
