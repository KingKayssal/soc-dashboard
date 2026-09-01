import React, { useEffect, useState } from "react";
import { HealthResponse } from "../types";

interface HeaderProps {
  health: HealthResponse | null;
  healthError: string | null;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export function Header({ health, healthError, onRefresh, isRefreshing }: HeaderProps) {
  const [utcTime, setUtcTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getHealthDotClass = () => {
    if (healthError) return "error";
    if (!health) return "";
    if (health.status === "ok") return "ok";
    if (health.status === "degraded") return "degraded";
    return "error";
  };

  const getHealthTooltip = () => {
    if (healthError) return `Backend unreachable: ${healthError}`;
    if (!health) return "Checking system health...";
    const pg = health.postgres_reachable ?? health.postgres_configured ?? false;
    const rd = health.redis_reachable ?? health.redis_configured ?? false;
    const wz = health.wazuh_configured ?? false;
    return `Status: ${health.status.toUpperCase()} | Postgres: ${pg ? "Connected" : "Down"} | Redis: ${rd ? "Connected" : "Down"} | Wazuh: ${wz ? "Configured" : "Missing"}`;
  };

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="brand-badge">
          <span>🛡️ SOC Sentinel</span>
          <span className="brand-tag">MVP</span>
        </div>
      </div>

      <div className="header-right">
        {/* Health status indicator */}
        <div className="health-strip" title={getHealthTooltip()}>
          <div className={`health-dot ${getHealthDotClass()}`} />
          <span>
            {healthError
              ? "Backend Offline"
              : health
              ? `Backend: ${health.status}`
              : "Checking..."}
          </span>
        </div>

        {/* Real-time UTC clock */}
        <div className="clock-display" title="System Time (UTC)">
          ⏱️ {utcTime}
        </div>

        {/* Refresh Button */}
        <button
          className="btn btn-secondary btn-sm"
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh Alerts and Health"
        >
          {isRefreshing ? "⏳ Refreshing..." : "🔄 Refresh"}
        </button>
      </div>
    </header>
  );
}
