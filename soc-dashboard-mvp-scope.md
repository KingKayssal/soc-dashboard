# SOC Dashboard — MVP Scope Document

**Phase:** 1 — Architecture & Scoping
**Status:** Draft
**Owner:** Fayssal

---

## 1. Problem statement

Build a working SOC monitoring dashboard on top of a home lab, learning SOC analyst workflows and detection engineering along the way. The near-term goal is a functioning MVP, not an enterprise-grade product.

## 2. Decision: build vs. integrate

**Decision: integrate.** Wazuh is already installed and will serve as the SIEM core — agent-based collection, log decoding/normalization, correlation rules, and indexed storage (via its bundled OpenSearch indexer). No custom ingestion pipeline (Kafka, hand-rolled parsers) is being built for the MVP.

This means the original roadmap's "multi-database strategy" (separate Elasticsearch + Kafka stream processing) is **deferred past MVP**. It becomes relevant later if/when log sources outgrow what a single Wazuh manager can absorb, or when ingesting sources Wazuh can't natively parse.

What gets built custom for the MVP is a thin application layer *on top of* Wazuh:
- A FastAPI backend that calls the Wazuh API and owns its own PostgreSQL database for things Wazuh doesn't track (case status, analyst notes, triage state, users)
- Redis for session/cache
- A React/TypeScript frontend that's purpose-built for SOC workflows, instead of using Wazuh's stock dashboard

## 3. Log sources (MVP: 3 sources, home lab)

| # | Source | Collection method | Why it's useful |
|---|--------|-------------------|------------------|
| 1 | Linux host(s) | Wazuh agent + auditd | Core Unix/Linux telemetry: auth, process exec, file integrity |
| 2 | Windows host(s) | Wazuh agent + Sysmon | Rich process/network/registry telemetry, maps well to ATT&CK |
| 3 | Network/firewall device (e.g. pfSense) | Syslog forwarded to Wazuh | Perimeter visibility — connections in/out, blocked traffic |

Rationale for this set: it covers the three telemetry classes every real SOC deals with (endpoint Linux, endpoint Windows, network perimeter) with minimal new infrastructure, since Wazuh already speaks all three natively.

## 4. Real-time vs. batch

**Real-time (streaming).** This isn't optional for a SOC use case — alerts need to reach the analyst view within seconds of the triggering event, not on a batch delay. Wazuh's manager processes events in near-real-time already; the custom layer must not introduce polling delays. The FastAPI backend should push new alerts to the frontend via WebSocket or Server-Sent Events rather than the frontend polling the Wazuh API on an interval.

## 5. Tenancy

**Single-tenant.** No multi-org/multi-tenant abstraction in the MVP. Users are analysts on one team, one set of log sources.

## 6. MVP feature scope

**In scope:**
- Ingest the 3 log sources above through Wazuh agents/syslog
- Wazuh's default rule set for baseline correlation/alerting (custom rules are a stretch goal, not required for MVP)
- Custom dashboard views:
  - Alert list (filterable, sortable, near-real-time)
  - Alert detail view (raw event, matched rule, MITRE ATT&CK tactic/technique if available)
  - Timeline view (chronological event stream for a host or time window)
  - Basic full-text/field search across indexed events
  - Minimal triage workflow: mark alert as new/investigating/closed, add a note

**Explicitly out of scope for MVP (V2+):**
- SOAR-style automated playbooks
- Full case management (linking multiple alerts into an investigation, evidence attachment)
- Threat intel enrichment (VirusTotal, AbuseIPDB, etc.)
- RBAC beyond a single analyst role
- Kafka/stream processing layer
- Multi-tenant support
- ML-based anomaly detection
- Compliance reporting
- Kubernetes/Helm deployment (docker-compose is sufficient for MVP)

## 7. Architecture

See accompanying diagram. Summary:

```
Linux hosts, Windows hosts, Network/firewall
        → Wazuh (agents, rules, indexer, API)
        → Custom API layer (FastAPI + PostgreSQL + Redis)
        → React dashboard (alerts, timeline, search, cases)
```

## 8. Open gaps to fill during Phase 1

- **Detection engineering knowledge**: identified gap — add SigmaHQ/sigma (GitHub) and MITRE ATT&CK Navigator to the learning list to understand how Wazuh's rule format relates to Sigma and ATT&CK technique mapping.
- **Alert data model**: needs its own design pass — what fields does the custom Postgres schema need beyond what Wazuh already returns (status, assignee, notes, linked-alert-ids for future case management)?
- **Docker-compose scaffold**: Wazuh + FastAPI + Postgres + Redis + React, wired together locally, is the concrete next milestone once this scope doc is settled.

## 9. Milestone (Phase 1 exit criteria)

- [x] Architecture diagram
- [x] Written MVP scope document (this file)
- [ ] Reviewed against actual Wazuh install (confirm agent versions, indexer access, API auth)
- [ ] Alert data model sketch (Phase 2)
