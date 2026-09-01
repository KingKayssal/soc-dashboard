"""Integration tests for FastAPI API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies import get_wazuh_client
from app.main import app
from app.wazuh.mock_client import MockWazuhClient

# Setup SQLite in-memory test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


mock_client_instance = MockWazuhClient(seed=42)


def override_get_wazuh_client():
    return mock_client_instance


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_wazuh_client] = override_get_wazuh_client

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "soc-dashboard-backend"
    assert "docs" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "postgres_reachable" in data
    assert "redis_reachable" in data
    assert "wazuh_configured" in data


def test_list_alerts():
    response = client.get("/api/alerts?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] >= 100
    assert data["limit"] == 10
    assert data["offset"] == 0

    first = data["items"][0]
    assert "id" in first
    assert "rule" in first
    assert "agent" in first
    assert first["triage_status"] == "new"


def test_get_alert_detail():
    list_resp = client.get("/api/alerts?limit=1")
    alert_id = list_resp.json()["items"][0]["id"]

    detail_resp = client.get(f"/api/alerts/{alert_id}")
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert data["id"] == alert_id
    assert "rule" in data
    assert "agent" in data
    assert "notes" in data
    assert isinstance(data["notes"], list)


def test_update_alert_triage():
    list_resp = client.get("/api/alerts?limit=1")
    alert_id = list_resp.json()["items"][0]["id"]

    # Patch triage status
    patch_resp = client.patch(
        f"/api/alerts/{alert_id}/triage",
        json={"status": "investigating", "severity_override": 14},
    )
    assert patch_resp.status_code == 200
    triage_data = patch_resp.json()
    assert triage_data["status"] == "investigating"
    assert triage_data["severity_override"] == 14

    # Verify status persisted on next GET
    detail_resp = client.get(f"/api/alerts/{alert_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["triage"]["status"] == "investigating"


def test_add_alert_note():
    list_resp = client.get("/api/alerts?limit=1")
    alert_id = list_resp.json()["items"][0]["id"]

    # Add note
    note_resp = client.post(
        f"/api/alerts/{alert_id}/notes",
        json={"content": "Investigating suspicious SSH brute force attempts."},
    )
    assert note_resp.status_code == 201
    note_data = note_resp.json()
    assert note_data["content"] == "Investigating suspicious SSH brute force attempts."
    assert note_data["wazuh_alert_id"] == alert_id

    # Verify note in detail
    detail_resp = client.get(f"/api/alerts/{alert_id}")
    assert len(detail_resp.json()["notes"]) == 1
    assert detail_resp.json()["notes"][0]["content"] == "Investigating suspicious SSH brute force attempts."


def test_list_agents():
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) == 5
    assert any(a["name"] == "linux-srv-prod01" for a in agents)


def test_get_stats_overview():
    resp = client.get("/api/stats/overview")
    assert resp.status_code == 200
    stats = resp.json()
    assert "alerts_last_24h" in stats
    assert "severity_breakdown" in stats
    assert "top_rules" in stats
    assert "top_agents" in stats


def test_case_lifecycle():
    # 1. Create Case
    create_resp = client.post(
        "/api/cases",
        json={
            "title": "Incident 2026-001: Active Credential Dumping",
            "description": "Multiple brute force attempts followed by shadow read.",
            "status": "open",
            "severity": "high",
            "wazuh_alert_ids": ["wazuh-alert-0001", "wazuh-alert-0002"],
        },
    )
    assert create_resp.status_code == 201
    case = create_resp.json()
    case_id = case["id"]
    assert case["title"] == "Incident 2026-001: Active Credential Dumping"
    assert len(case["case_alerts"]) == 2

    # 2. Add Note to Case
    note_resp = client.post(
        f"/api/cases/{case_id}/notes",
        json={"content": "Quarantined host and rotated credentials."},
    )
    assert note_resp.status_code == 201

    # 3. Update Case to Closed
    update_resp = client.patch(
        f"/api/cases/{case_id}",
        json={"status": "closed"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "closed"
    assert update_resp.json()["resolved_at"] is not None

    # 4. List Cases
    list_resp = client.get("/api/cases")
    assert list_resp.status_code == 200
    cases = list_resp.json()
    assert any(c["id"] == case_id for c in cases)
