"""Tests for MockWazuhClient."""
import pytest
from app.wazuh.mock_client import MockWazuhClient


@pytest.mark.asyncio
async def test_mock_client_alert_generation():
    client = MockWazuhClient(seed=42)
    alerts, total = await client.get_alerts(limit=50, offset=0)

    assert total >= 100
    assert len(alerts) == 50

    sample = alerts[0]
    assert "id" in sample
    assert "timestamp" in sample
    assert "rule" in sample
    assert "agent" in sample
    assert "level" in sample["rule"]
    assert "mitre" in sample["rule"]
    assert "id" in sample["agent"]
    assert "name" in sample["agent"]


@pytest.mark.asyncio
async def test_mock_client_filtering():
    client = MockWazuhClient(seed=42)

    # Filter by severity
    high_alerts, total_high = await client.get_alerts(limit=100, severity_min=10)
    assert total_high > 0
    assert all(a["rule"]["level"] >= 10 for a in high_alerts)

    # Filter by agent
    agent_alerts, total_agent = await client.get_alerts(limit=100, agent_id="001")
    assert total_agent > 0
    assert all(a["agent"]["id"] == "001" for a in agent_alerts)

    # Filter by rule
    rule_alerts, total_rule = await client.get_alerts(limit=100, rule_id="5710")
    assert total_rule > 0
    assert all(a["rule"]["id"] == "5710" for a in rule_alerts)


@pytest.mark.asyncio
async def test_mock_client_pagination():
    client = MockWazuhClient(seed=42)

    page1, total1 = await client.get_alerts(limit=10, offset=0)
    page2, total2 = await client.get_alerts(limit=10, offset=10)

    assert total1 == total2
    assert len(page1) == 10
    assert len(page2) == 10
    assert page1[0]["id"] != page2[0]["id"]


@pytest.mark.asyncio
async def test_mock_client_get_alert():
    client = MockWazuhClient(seed=42)
    alerts, _ = await client.get_alerts(limit=1, offset=0)
    first_id = alerts[0]["id"]

    alert = await client.get_alert(first_id)
    assert alert is not None
    assert alert["id"] == first_id

    non_existent = await client.get_alert("non-existent-alert-id")
    assert non_existent is None


@pytest.mark.asyncio
async def test_mock_client_agents_and_stats():
    client = MockWazuhClient(seed=42)

    agents = await client.get_agents()
    assert len(agents) == 5
    agent_names = [a["name"] for a in agents]
    assert "linux-srv-prod01" in agent_names
    assert "win-desktop-fin01" in agent_names
    assert "pfsense-firewall" in agent_names

    stats = await client.get_stats_overview()
    assert "alerts_last_24h" in stats
    assert "severity_breakdown" in stats
    assert "top_rules" in stats
    assert "top_agents" in stats
    assert stats["alerts_last_24h"] > 0
    assert sum(stats["severity_breakdown"].values()) == stats["alerts_last_24h"]
