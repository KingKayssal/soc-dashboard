import React, { useCallback, useEffect, useState } from "react";
import { fetchHealth } from "./api/client";
import { AlertsView } from "./components/Alerts/AlertsView";
import { ComingSoon } from "./components/Common/ComingSoon";
import { Header } from "./components/Header";
import { NavTab, Sidebar } from "./components/Sidebar";
import { HealthResponse } from "./types";

export default function App() {
  const [activeTab, setActiveTab] = useState<NavTab>("alerts");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [totalAlerts, setTotalAlerts] = useState<number>(0);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const checkHealth = useCallback(async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
      setHealthError(null);
    } catch (err: unknown) {
      setHealthError((err as Error).message || "Could not reach backend");
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    // Coarse 60s health check interval
    const interval = setInterval(checkHealth, 60000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await checkHealth();
    setRefreshTrigger((prev) => prev + 1);
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <div className="app-container">
      {/* Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        totalAlerts={totalAlerts}
      />

      {/* Main Layout Area */}
      <div className="main-layout">
        {/* Top Header with live status and clock */}
        <Header
          health={health}
          healthError={healthError}
          onRefresh={handleManualRefresh}
          isRefreshing={isRefreshing}
        />

        {/* Content Area */}
        <main className="content-area">
          {activeTab === "alerts" && (
            <AlertsView
              onTotalAlertsChange={setTotalAlerts}
              refreshTrigger={refreshTrigger}
            />
          )}

          {activeTab === "overview" && (
            <ComingSoon
              title="Overview & Metrics Dashboard"
              description="High-level threat KPI metrics, 24-hour alert trend volume charts, and MITRE ATT&CK heatmap will be available in Phase 4."
            />
          )}

          {activeTab === "agents" && (
            <ComingSoon
              title="Wazuh Agent Fleet Management"
              description="Monitored endpoint status (Linux, Windows, pfSense), agent version inventory, and keepalive heartbeat health are coming in Phase 4."
            />
          )}

          {activeTab === "cases" && (
            <ComingSoon
              title="Incident & Case Management"
              description="Full investigation case management, alert aggregation, and analyst assignment dossiers will be available in Phase 4."
            />
          )}
        </main>
      </div>
    </div>
  );
}
