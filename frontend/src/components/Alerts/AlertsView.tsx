import React, { useCallback, useEffect, useState } from "react";
import { fetchAlerts } from "../../api/client";
import { AlertFilters, AlertListItem, TriageStatus } from "../../types";
import { ErrorMessage, LoadingSpinner } from "../Common/ComingSoon";
import { Pagination } from "../Common/Pagination";
import { AlertDetailDrawer } from "./AlertDetailDrawer";
import { AlertFiltersBar } from "./AlertFiltersBar";
import { AlertTable } from "./AlertTable";

const DEFAULT_FILTERS: AlertFilters = {
  status: "all",
  severityMin: "",
  agentId: "",
  ruleId: "",
  search: "",
};

interface AlertsViewProps {
  onTotalAlertsChange?: (total: number) => void;
  refreshTrigger?: number;
}

export function AlertsView({ onTotalAlertsChange, refreshTrigger }: AlertsViewProps) {
  const [alerts, setAlerts] = useState<AlertListItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [limit, setLimit] = useState<number>(25);
  const [offset, setOffset] = useState<number>(0);
  const [filters, setFilters] = useState<AlertFilters>(DEFAULT_FILTERS);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Selected alert for drawer
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchAlerts({
        limit,
        offset,
        severity_min: typeof filters.severityMin === "number" ? filters.severityMin : undefined,
        status: filters.status !== "all" ? filters.status : undefined,
        agent_id: filters.agentId || undefined,
        rule_id: filters.ruleId || undefined,
      });

      setAlerts(resp.items);
      setTotal(resp.total);
      if (onTotalAlertsChange) {
        onTotalAlertsChange(resp.total);
      }
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to fetch alerts from backend");
    } finally {
      setLoading(false);
    }
  }, [limit, offset, filters.severityMin, filters.status, filters.agentId, filters.ruleId, onTotalAlertsChange]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts, refreshTrigger]);

  const handleFilterChange = (newFilters: AlertFilters) => {
    setFilters(newFilters);
    setOffset(0); // Reset to first page on filter change
  };

  const handleResetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setOffset(0);
  };

  const handlePageChange = (newOffset: number) => {
    setOffset(newOffset);
  };

  const handleLimitChange = (newLimit: number) => {
    setLimit(newLimit);
    setOffset(0);
  };

  const handleTriageUpdated = (alertId: string, newStatus: TriageStatus) => {
    // Optimistic update of local table state
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === alertId
          ? {
              ...a,
              triage_status: newStatus,
              triage: a.triage
                ? { ...a.triage, status: newStatus }
                : {
                    id: "temp",
                    wazuh_alert_id: alertId,
                    status: newStatus,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                  },
            }
          : a
      )
    );
  };

  // Client-side text filter for search query
  const displayedAlerts = alerts.filter((a) => {
    if (!filters.search.trim()) return true;
    const query = filters.search.toLowerCase();
    const desc = (a.rule?.description || "").toLowerCase();
    const ruleId = (a.rule?.id || "").toLowerCase();
    const agentName = (a.agent?.name || "").toLowerCase();
    const alertId = (a.id || "").toLowerCase();
    return (
      desc.includes(query) ||
      ruleId.includes(query) ||
      agentName.includes(query) ||
      alertId.includes(query)
    );
  });

  return (
    <div className="alerts-view">
      {/* Header Info */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>🚨 Security Alerts</span>
            <span className="title-count-chip">{total} Indexed</span>
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
            Real-time telemetry stream from Wazuh SIEM with PostgreSQL triage overlay.
          </p>
        </div>
      </div>

      {/* Filter Controls */}
      <AlertFiltersBar
        filters={filters}
        onChange={handleFilterChange}
        onReset={handleResetFilters}
      />

      {/* Error state */}
      {error && <ErrorMessage message={error} onRetry={loadAlerts} />}

      {/* Table & Loading */}
      {loading ? (
        <div className="table-card">
          <LoadingSpinner message="Querying Wazuh alerts and triage status..." />
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <AlertTable
            alerts={displayedAlerts}
            selectedAlertId={selectedAlertId}
            onSelectAlert={(a) => setSelectedAlertId(a.id)}
          />

          {/* Pagination */}
          <Pagination
            total={total}
            limit={limit}
            offset={offset}
            onPageChange={handlePageChange}
            onLimitChange={handleLimitChange}
          />
        </div>
      )}

      {/* Detail Slide-Over Drawer */}
      {selectedAlertId && (
        <AlertDetailDrawer
          alertId={selectedAlertId}
          onClose={() => setSelectedAlertId(null)}
          onTriageUpdated={handleTriageUpdated}
        />
      )}
    </div>
  );
}
