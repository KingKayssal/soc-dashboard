"""FastAPI routers package."""
from app.routers.agents import router as agents_router
from app.routers.alerts import router as alerts_router
from app.routers.cases import router as cases_router
from app.routers.stats import router as stats_router

__all__ = ["agents_router", "alerts_router", "cases_router", "stats_router"]
