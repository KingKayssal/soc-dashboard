# SOC Dashboard

A self-directed build of a SOC monitoring dashboard. See `docs/mvp-scope.md` for
the full Phase 1 scope document and architecture rationale.

## Repo layout

```
/soc-dashboard
  /ingestion   collectors, parsers (placeholder — Wazuh handles this for MVP)
  /backend     FastAPI service: talks to Wazuh API, owns Postgres for app data
  /frontend    React/TypeScript dashboard UI
  /infra       docker-compose, later: k8s manifests, terraform
  /docs        scope docs, architecture notes
```

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin on Linux)
- Git
- A running Wazuh manager somewhere reachable on your network, with the API enabled
  (this stack does not containerize Wazuh — it connects to your existing install)

## Setup

1. Copy the env template and fill in real values:
   ```bash
   cp .env.example .env
   # edit .env: set POSTGRES_PASSWORD and your real WAZUH_API_URL / credentials
   ```

2. Bring up the stack:
   ```bash
   cd infra
   docker compose up --build
   ```

3. Verify:
   - Backend health check: http://localhost:8000/health
   - Backend API docs: http://localhost:8000/docs
   - Frontend: http://localhost:5173

   The frontend calls the backend's `/health` endpoint on load and shows whether
   Postgres, Redis, and the Wazuh API URL are configured. This is the Phase 2
   milestone — a working local dev loop, not real dashboard functionality yet.

## What's stubbed vs. real

| Component | State |
|---|---|
| Postgres, Redis | Real, running containers |
| Backend | Real FastAPI service, one real `/health` endpoint, no business logic yet |
| Frontend | Real Vite/React app, one placeholder page |
| Wazuh | Not containerized — must already be running in your lab; backend just points at it |
| Ingestion | Empty — Wazuh agents/syslog handle this directly, no custom code needed for MVP |

## Next steps (Phase 3)

- Design the Postgres schema for cases/alerts/triage state
- Wire the backend to actually call the Wazuh API (auth, fetch alerts)
- Replace the frontend placeholder with a real alert list view
