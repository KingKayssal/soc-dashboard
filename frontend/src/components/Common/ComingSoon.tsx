import React from "react";

export function ComingSoon({ title, description }: { title: string; description: string }) {
  return (
    <div className="coming-soon-card">
      <div
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "50%",
          backgroundColor: "rgba(56, 189, 248, 0.1)",
          border: "1px solid rgba(56, 189, 248, 0.3)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "1.5rem",
        }}
      >
        🛡️
      </div>
      <h2>{title}</h2>
      <p>{description}</p>
      <div className="badge" style={{ backgroundColor: "var(--bg-subtle)", color: "var(--accent-cyan)" }}>
        Planned for Phase 4
      </div>
    </div>
  );
}

export function LoadingSpinner({ message = "Loading alerts..." }: { message?: string }) {
  return (
    <div className="state-container">
      <div className="spinner" />
      <span style={{ fontSize: "0.85rem" }}>{message}</span>
    </div>
  );
}

export function ErrorMessage({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      className="state-container"
      style={{
        backgroundColor: "rgba(239, 68, 68, 0.08)",
        border: "1px solid rgba(239, 68, 68, 0.25)",
        borderRadius: "var(--radius-lg)",
        margin: "1rem 0",
      }}
    >
      <div style={{ color: "var(--sev-critical-text)", fontWeight: 600 }}>⚠️ Connection / API Error</div>
      <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", maxWidth: "600px", textAlign: "center" }}>
        {message}
      </div>
      {onRetry && (
        <button className="btn btn-secondary btn-sm" onClick={onRetry} style={{ marginTop: "0.5rem" }}>
          🔄 Retry Request
        </button>
      )}
    </div>
  );
}
