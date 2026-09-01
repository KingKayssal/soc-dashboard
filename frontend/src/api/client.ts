/**
 * API client communicating with the FastAPI backend.
 */
import {
  AlertDetail,
  AlertListResponse,
  AlertTriage,
  AnalystNote,
  HealthResponse,
  TriageStatus,
} from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorMsg = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  return handleResponse<HealthResponse>(res);
}

export async function fetchAlerts(params: {
  limit?: number;
  offset?: number;
  severity_min?: number;
  status?: string;
  agent_id?: string;
  rule_id?: string;
  since?: string;
}): Promise<AlertListResponse> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));
  if (params.severity_min !== undefined && params.severity_min > 0)
    query.set("severity_min", String(params.severity_min));
  if (params.status && params.status !== "all") query.set("status", params.status);
  if (params.agent_id && params.agent_id.trim()) query.set("agent_id", params.agent_id.trim());
  if (params.rule_id && params.rule_id.trim()) query.set("rule_id", params.rule_id.trim());
  if (params.since) query.set("since", params.since);

  const url = `${API_BASE}/api/alerts${query.toString() ? `?${query.toString()}` : ""}`;
  const res = await fetch(url);
  return handleResponse<AlertListResponse>(res);
}

export async function fetchAlertDetail(alertId: string): Promise<AlertDetail> {
  const res = await fetch(`${API_BASE}/api/alerts/${encodeURIComponent(alertId)}`);
  return handleResponse<AlertDetail>(res);
}

export async function updateAlertTriage(
  alertId: string,
  payload: {
    status?: TriageStatus;
    severity_override?: number | null;
    assigned_to_id?: string | null;
  }
): Promise<AlertTriage> {
  const res = await fetch(`${API_BASE}/api/alerts/${encodeURIComponent(alertId)}/triage`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<AlertTriage>(res);
}

export async function addAlertNote(
  alertId: string,
  payload: { content: string; author_id?: string }
): Promise<AnalystNote> {
  const res = await fetch(`${API_BASE}/api/alerts/${encodeURIComponent(alertId)}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<AnalystNote>(res);
}
