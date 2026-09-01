import React from "react";
import { TriageStatus } from "../../types";

export function SeverityBadge({ level }: { level: number }) {
  let label = "Low";
  let className = "badge-sev-low";

  if (level >= 12) {
    label = "Critical";
    className = "badge-sev-critical";
  } else if (level >= 8) {
    label = "High";
    className = "badge-sev-high";
  } else if (level >= 4) {
    label = "Medium";
    className = "badge-sev-medium";
  }

  return (
    <span className={`badge ${className}`} title={`Rule Severity Level ${level}`}>
      Lvl {level} • {label}
    </span>
  );
}

export function TriageBadge({ status }: { status: TriageStatus | string }) {
  const displayStatus = (status || "new").replace("_", " ");
  const statusClass = status ? status.toLowerCase() : "new";

  return (
    <span className={`badge badge-triage ${statusClass}`}>
      {displayStatus}
    </span>
  );
}
