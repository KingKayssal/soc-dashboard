"""Explicit acceptance criteria verification script."""
import json
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies import get_wazuh_client
from app.main import app
from app.wazuh.mock_client import MockWazuhClient

# Setup SQLite test DB
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


mock_client = MockWazuhClient(seed=42)
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_wazuh_client] = lambda: mock_client

client = TestClient(app)


def run_all_criteria():
    print("=" * 60)
    print("RUNNING ACCEPTANCE CRITERIA VERIFICATION")
    print("=" * 60)

    # 1. Health check
    print("\n--- Criteria 2: /health Endpoint ---")
    resp = client.get("/health")
    print(f"Status Code: {resp.status_code}")
    print(f"Response Body: {json.dumps(resp.json(), indent=2)}")
    assert resp.status_code == 200
    health_data = resp.json()
    assert "postgres_reachable" in health_data
    assert "redis_reachable" in health_data
    assert "wazuh_configured" in health_data
    assert "postgres_configured" in health_data
    assert "redis_configured" in health_data

    # 2. Alerts listing
    print("\n--- Criteria 3: GET /api/alerts?limit=10 ---")
    resp = client.get("/api/alerts?limit=10")
    print(f"Status Code: {resp.status_code}")
    data = resp.json()
    print(f"Total Alerts Count: {data['total']}")
    print(f"Items Returned: {len(data['items'])}")
    print("\nSample Alerts Summary (Telemetry Sources & Severities):")
    for i, item in enumerate(data["items"][:5], 1):
        print(
            f"  {i}. ID: {item['id']} | Agent: {item['agent']['name']} ({item['agent']['ip']}) | "
            f"Rule: {item['rule']['id']} (Lvl {item['rule']['level']}) | "
            f"MITRE: {item['rule'].get('mitre')} | Status: {item['triage_status']}"
        )
    assert resp.status_code == 200
    assert len(data["items"]) == 10
    assert data["total"] >= 100

    target_alert_id = data["items"][0]["id"]

    # 3. Alert detail
    print(f"\n--- Criteria 4: GET /api/alerts/{target_alert_id} (Detail) ---")
    resp = client.get(f"/api/alerts/{target_alert_id}")
    print(f"Status Code: {resp.status_code}")
    detail = resp.json()
    print(f"Alert ID: {detail['id']}")
    print(f"Timestamp: {detail['timestamp']}")
    print(f"Location: {detail['location']}")
    print(f"Full Log: {detail['full_log']}")
    print(f"Data: {json.dumps(detail['data'])}")
    print(f"Triage: {detail['triage']}")
    print(f"Notes: {detail['notes']}")
    assert resp.status_code == 200
    assert detail["id"] == target_alert_id

    # 4. PATCH triage status
    print(f"\n--- Criteria 5: PATCH /api/alerts/{target_alert_id}/triage ---")
    patch_payload = {"status": "investigating", "severity_override": 12}
    print(f"Sending Payload: {patch_payload}")
    resp = client.patch(f"/api/alerts/{target_alert_id}/triage", json=patch_payload)
    print(f"Status Code: {resp.status_code}")
    print(f"Triage Response: {json.dumps(resp.json(), indent=2)}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "investigating"
    assert resp.json()["severity_override"] == 12

    # 5. Confirm persistence on next GET
    print(f"\n--- Criteria 5 (cont): Confirm Persistence with GET /api/alerts/{target_alert_id} ---")
    resp = client.get(f"/api/alerts/{target_alert_id}")
    detail_after = resp.json()
    print(f"Status Code: {resp.status_code}")
    print(f"Triage in Alert Detail: {json.dumps(detail_after['triage'], indent=2)}")
    assert resp.status_code == 200
    assert detail_after["triage"] is not None
    assert detail_after["triage"]["status"] == "investigating"

    # Also verify in list_alerts
    list_resp = client.get("/api/alerts?limit=10")
    first_item = list_resp.json()["items"][0]
    assert first_item["id"] == target_alert_id
    assert first_item["triage_status"] == "investigating"
    print(f"Verified in List Alerts: triage_status is now '{first_item['triage_status']}'")

    # 6. OpenAPI /docs schema
    print("\n--- Criteria 6: OpenAPI Schema Verification ---")
    resp = client.get("/openapi.json")
    openapi = resp.json()
    paths = list(openapi["paths"].keys())
    print(f"Discovered Endpoints ({len(paths)} routes):")
    for p in paths:
        methods = list(openapi["paths"][p].keys())
        print(f"  - {methods[0].upper()} {p}")
    assert "/api/alerts" in paths
    assert "/api/alerts/{wazuh_alert_id}" in paths
    assert "/api/alerts/{wazuh_alert_id}/triage" in paths
    assert "/api/alerts/{wazuh_alert_id}/notes" in paths
    assert "/api/agents" in paths
    assert "/api/stats/overview" in paths
    assert "/api/cases" in paths

    print("\n" + "=" * 60)
    print("ALL ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_criteria()
