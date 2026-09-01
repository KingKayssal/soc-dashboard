/**
 * Shared TypeScript interfaces for SOC Dashboard.
 */

export type TriageStatus = "new" | "investigating" | "false_positive" | "resolved";

export type MitreAttack = {
  id: string[];
  tactic: string[];
};

export type AlertRule = {
  id: string;
  description: string;
  level: number;
  mitre?: MitreAttack | null;
};

export type AlertAgent = {
  id: string;
  name: string;
  ip?: string | null;
};

export type AlertTriage = {
  id: string;
  wazuh_alert_id: string;
  status: TriageStatus;
  severity_override?: number | null;
  assigned_to_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type AlertListItem = {
  id: string;
  timestamp: string;
  rule: AlertRule;
  agent: AlertAgent;
  location?: string | null;
  triage?: AlertTriage | null;
  triage_status: TriageStatus;
};

export type AlertListResponse = {
  items: AlertListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type AnalystNote = {
  id: string;
  wazuh_alert_id?: string | null;
  case_id?: string | null;
  author_id?: string | null;
  content: string;
  created_at: string;
};

export type AlertDetail = {
  id: string;
  timestamp: string;
  rule: {
    id: string;
    description: string;
    level: number;
    mitre?: MitreAttack | null;
    [key: string]: unknown;
  };
  agent: {
    id: string;
    name: string;
    ip?: string | null;
    [key: string]: unknown;
  };
  location?: string | null;
  full_log?: string | null;
  data?: Record<string, unknown> | null;
  triage?: AlertTriage | null;
  notes: AnalystNote[];
};

export type HealthResponse = {
  status: string;
  postgres_reachable?: boolean;
  redis_reachable?: boolean;
  wazuh_configured?: boolean;
  postgres_configured?: boolean;
  redis_configured?: boolean;
};

export type AlertFilters = {
  status: string;
  severityMin: number | "";
  agentId: string;
  ruleId: string;
  search: string;
};
