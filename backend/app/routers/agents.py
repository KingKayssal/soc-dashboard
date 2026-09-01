"""Agents API endpoints."""
from fastapi import APIRouter, Depends

from app.dependencies import get_wazuh_client
from app.schemas.agent import AgentResponse
from app.wazuh.client import WazuhClient

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    wazuh_client: WazuhClient = Depends(get_wazuh_client),
) -> list[AgentResponse]:
    """Fetch registered Wazuh agents and their current connection status."""
    agents_raw = await wazuh_client.get_agents()
    return [AgentResponse.model_validate(a) for a in agents_raw]
