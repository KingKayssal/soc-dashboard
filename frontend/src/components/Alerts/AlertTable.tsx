import React from "react";
import { AlertListItem } from "../../types";
import { SeverityBadge, TriageBadge } from "../Common/Badge";

interface AlertTableProps {
  alerts: AlertListItem[];
  selectedAlertId: string | null;
  onSelectAlert: (alert: AlertListItem) => void;
}

function formatRelativeTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (isNaN(diffSeconds)) return isoString;
    if (diffSeconds < 60) return `${Math.max(1, diffSeconds)}s ago`;
    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  } catch {
    return isoString;
  }
}

function formatFullUtc(isoString: string): string {
  try {
    return new Date(isoString).toISOString();
  } catch {
    return isoString;
  }
}

export function AlertTable({ alerts, selectedAlertId, onSelectAlert }: AlertTableProps) {
  if (alerts.length === 0) {
    return (
      <div className="table-card">
        <div className="state-container">
          <div style={{ fontSize: "1.5rem" }}>🔍</div>
          <div>No alerts found matching your filters.</div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Try clearing or adjusting the search and severity filters.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="table-card">
      <div className="table-responsive">
        <table className="alert-table">
          <thead>
            <tr>
              <th style={{ width: "110px" }}>Time</th>
              <th style={{ width: "120px" }}>Severity</th>
              <th>Rule & Description</th>
              <th style={{ width: "180px" }}>Host / Agent</th>
              <th style={{ width: "180px" }}>MITRE ATT&CK</th>
              <th style={{ width: "130px" }}>Triage Status</th>
              <th style={{ width: "90px", textAlign: "right" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => {
              const isSelected = selectedAlertId === alert.id;
              const rule = alert.rule || {};
              const agent = alert.agent || {};
              const mitre = rule.mitre;
              const tactics = mitre?.tactic || [];
              const techIds = mitre?.id || [];

              return (
                <tr
                  key={alert.id}
                  className={isSelected ? "selected" : ""}
                  onClick={() => onSelectAlert(alert)}
                >
                  {/* Timestamp */}
                  <td title={formatFullUtc(alert.timestamp)}>
                    <div style={{ fontWeight: 500 }}>{formatRelativeTime(alert.timestamp)}</div>
                    <div className="mono-cell" style={{ fontSize: "0.68rem" }}>
                      {alert.timestamp.substring(11, 19)} UTC
                    </div>
                  </td>

                  {/* Severity Badge */}
                  <td>
                    <SeverityBadge level={rule.level ?? 1} />
                  </td>

                  {/* Rule & Description */}
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.15rem" }}>
                      <span className="mono-cell" style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>
                        #{rule.id}
                      </span>
                    </div>
                    <div style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                      {rule.description || "Unspecified alert rule"}
                    </div>
                  </td>

                  {/* Agent */}
                  <td>
                    <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                      {agent.name || "Unknown Agent"}
                    </div>
                    <div className="mono-cell" style={{ fontSize: "0.72rem" }}>
                      {agent.ip || `ID: ${agent.id}`}
                    </div>
                  </td>

                  {/* MITRE ATT&CK */}
                  <td>
                    {tactics.length > 0 || techIds.length > 0 ? (
                      <div>
                        {tactics.map((t, idx) => (
                          <span key={`tactic-${idx}`} className="mitre-badge" title="MITRE Tactic">
                            {t}
                          </span>
                        ))}
                        {techIds.map((tId, idx) => (
                          <span
                            key={`tech-${idx}`}
                            className="mitre-badge"
                            style={{ color: "var(--accent-cyan)" }}
                            title="MITRE Technique"
                          >
                            {tId}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>—</span>
                    )}
                  </td>

                  {/* Triage Status */}
                  <td>
                    <TriageBadge status={alert.triage_status} />
                  </td>

                  {/* Action */}
                  <td style={{ textAlign: "right" }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectAlert(alert);
                      }}
                      title="Inspect Alert Details"
                    >
                      Inspect →
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
