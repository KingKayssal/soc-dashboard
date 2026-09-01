"""Statistics and overview metrics API endpoints."""
from fastapi import APIRouter, Depends

from app.dependencies import get_wazuh_client
from app.schemas.stats import StatsOverviewResponse
from app.wazuh.client import WazuhClient

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverviewResponse)
async def get_overview_stats(
    wazuh_client: WazuhClient = Depends(get_wazuh_client),
) -> StatsOverviewResponse:
    """Fetch high-level SOC dashboard stats: alerts 24h, severity breakdown, top rules, top agents."""
    stats = await wazuh_client.get_stats_overview()
    return StatsOverviewResponse.model_validate(stats)
