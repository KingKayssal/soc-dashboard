import React from "react";

export type NavTab = "alerts" | "overview" | "agents" | "cases";

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  totalAlerts?: number;
}

export function Sidebar({ activeTab, onSelectTab, totalAlerts }: SidebarProps) {
  return (
    <aside className="app-sidebar">
      <nav className="sidebar-nav">
        <button
          className={`nav-item ${activeTab === "alerts" ? "active" : ""}`}
          onClick={() => onSelectTab("alerts")}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            🚨 Alerts
          </span>
          {totalAlerts !== undefined && totalAlerts > 0 && (
            <span className="nav-item-badge">{totalAlerts}</span>
          )}
        </button>

        <button
          className={`nav-item ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => onSelectTab("overview")}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            📊 Overview
          </span>
          <span className="nav-item-badge" style={{ fontSize: "0.65rem" }}>Soon</span>
        </button>

        <button
          className={`nav-item ${activeTab === "agents" ? "active" : ""}`}
          onClick={() => onSelectTab("agents")}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            💻 Agents
          </span>
          <span className="nav-item-badge" style={{ fontSize: "0.65rem" }}>Soon</span>
        </button>

        <button
          className={`nav-item ${activeTab === "cases" ? "active" : ""}`}
          onClick={() => onSelectTab("cases")}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            📁 Cases
          </span>
          <span className="nav-item-badge" style={{ fontSize: "0.65rem" }}>Soon</span>
        </button>
      </nav>

      <div className="sidebar-footer">
        <div><strong>SIEM Core:</strong> Wazuh</div>
        <div style={{ marginTop: "0.25rem" }}>Mode: Mock (Synthetic)</div>
      </div>
    </aside>
  );
}
