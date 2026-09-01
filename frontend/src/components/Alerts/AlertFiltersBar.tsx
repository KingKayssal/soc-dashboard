import React from "react";
import { AlertFilters } from "../../types";

interface AlertFiltersBarProps {
  filters: AlertFilters;
  onChange: (newFilters: AlertFilters) => void;
  onReset: () => void;
}

export function AlertFiltersBar({ filters, onChange, onReset }: AlertFiltersBarProps) {
  const hasActiveFilters =
    filters.status !== "all" ||
    filters.severityMin !== "" ||
    filters.agentId !== "" ||
    filters.ruleId !== "" ||
    filters.search !== "";

  return (
    <div className="filter-bar">
      {/* Triage Status Filter */}
      <div className="filter-group">
        <label className="filter-label">Triage:</label>
        <select
          className="filter-select"
          value={filters.status}
          onChange={(e) => onChange({ ...filters, status: e.target.value })}
        >
          <option value="all">All Statuses</option>
          <option value="new">New</option>
          <option value="investigating">Investigating</option>
          <option value="false_positive">False Positive</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      {/* Min Severity Filter */}
      <div className="filter-group">
        <label className="filter-label">Min Severity:</label>
        <select
          className="filter-select"
          value={filters.severityMin}
          onChange={(e) =>
            onChange({
              ...filters,
              severityMin: e.target.value === "" ? "" : Number(e.target.value),
            })
          }
        >
          <option value="">All Levels (1-15)</option>
          <option value={4}>Level ≥ 4 (Medium+)</option>
          <option value={8}>Level ≥ 8 (High+)</option>
          <option value={12}>Level ≥ 12 (Critical)</option>
        </select>
      </div>

      {/* Agent Filter */}
      <div className="filter-group">
        <label className="filter-label">Agent ID:</label>
        <select
          className="filter-select"
          value={filters.agentId}
          onChange={(e) => onChange({ ...filters, agentId: e.target.value })}
        >
          <option value="">All Agents</option>
          <option value="001">001 (linux-srv-prod01)</option>
          <option value="002">002 (win-desktop-fin01)</option>
          <option value="003">003 (pfsense-firewall)</option>
          <option value="004">004 (dev-linux-node02)</option>
        </select>
      </div>

      {/* Keyword / Rule Search */}
      <div className="filter-group filter-search">
        <label className="filter-label">Search:</label>
        <input
          type="text"
          className="filter-input"
          style={{ width: "100%" }}
          placeholder="Filter by keyword, rule, host, or ID..."
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
        />
      </div>

      {/* Clear Filters Button */}
      {hasActiveFilters && (
        <button
          className="btn btn-secondary btn-sm"
          onClick={onReset}
          title="Reset all filters"
        >
          ✕ Clear
        </button>
      )}
    </div>
  );
}
