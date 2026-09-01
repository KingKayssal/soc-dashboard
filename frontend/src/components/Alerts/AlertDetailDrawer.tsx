import React, { useEffect, useState } from "react";
import { addAlertNote, fetchAlertDetail, updateAlertTriage } from "../../api/client";
import { AlertDetail, TriageStatus } from "../../types";
import { SeverityBadge, TriageBadge } from "../Common/Badge";
import { LoadingSpinner } from "../Common/ComingSoon";

interface AlertDetailDrawerProps {
  alertId: string | null;
  onClose: () => void;
  onTriageUpdated: (alertId: string, newStatus: TriageStatus) => void;
}

export function AlertDetailDrawer({
  alertId,
  onClose,
  onTriageUpdated,
}: AlertDetailDrawerProps) {
  const [detail, setDetail] = useState<AlertDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Triage state
  const [savingTriage, setSavingTriage] = useState<boolean>(false);
  const [triageSuccess, setTriageSuccess] = useState<boolean>(false);

  // Note state
  const [noteContent, setNoteContent] = useState<string>("");
  const [submittingNote, setSubmittingNote] = useState<boolean>(false);
  const [noteError, setNoteError] = useState<string | null>(null);

  // Copy state
  const [copyLogSuccess, setCopyLogSuccess] = useState<boolean>(false);
  const [copyJsonSuccess, setCopyJsonSuccess] = useState<boolean>(false);
  const [showJsonData, setShowJsonData] = useState<boolean>(true);

  // Fetch alert detail on mount or when alertId changes
  useEffect(() => {
    if (!alertId) {
      setDetail(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchAlertDetail(alertId)
      .then((data) => {
        if (isMounted) {
          setDetail(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load alert details");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [alertId]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!alertId) return null;

  const currentStatus: TriageStatus =
    detail?.triage?.status ?? detail?.triage_status ?? "new";

  const handleStatusChange = async (newStatus: TriageStatus) => {
    if (!detail) return;
    setSavingTriage(true);
    setTriageSuccess(false);

    try {
      const updatedTriage = await updateAlertTriage(detail.id, { status: newStatus });
      setDetail((prev) =>
        prev
          ? {
              ...prev,
              triage: updatedTriage,
              triage_status: newStatus,
            }
          : null
      );
      onTriageUpdated(detail.id, newStatus);
      setTriageSuccess(true);
      setTimeout(() => setTriageSuccess(false), 2500);
    } catch (err: unknown) {
      alert(`Failed to update triage status: ${(err as Error).message}`);
    } finally {
      setSavingTriage(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!detail || !noteContent.trim()) return;

    setSubmittingNote(true);
    setNoteError(null);

    try {
      const createdNote = await addAlertNote(detail.id, {
        content: noteContent.trim(),
        author_id: "analyst-local",
      });
      // Append note immediately without full page reload
      setDetail((prev) =>
        prev
          ? {
              ...prev,
              notes: [createdNote, ...(prev.notes || [])],
            }
          : null
      );
      setNoteContent("");
    } catch (err: unknown) {
      setNoteError((err as Error).message || "Failed to add note");
    } finally {
      setSubmittingNote(false);
    }
  };

  const handleCopyLog = () => {
    if (!detail?.full_log) return;
    navigator.clipboard.writeText(detail.full_log);
    setCopyLogSuccess(true);
    setTimeout(() => setCopyLogSuccess(false), 2000);
  };

  const handleCopyJson = () => {
    if (!detail?.data) return;
    navigator.clipboard.writeText(JSON.stringify(detail.data, null, 2));
    setCopyJsonSuccess(true);
    setTimeout(() => setCopyJsonSuccess(false), 2000);
  };

  const rule = detail?.rule || {};
  const agent = detail?.agent || {};
  const mitre = rule.mitre;
  const tactics = mitre?.tactic || [];
  const techIds = mitre?.id || [];

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="drawer-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
              <span className="mono-cell" style={{ color: "var(--accent-cyan)", fontWeight: 700 }}>
                {alertId}
              </span>
            </div>
            <h3 className="drawer-title">{rule.description || "Alert Details"}</h3>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={onClose} title="Close (Esc)">
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="drawer-body">
          {loading && <LoadingSpinner message="Loading alert details..." />}

          {error && (
            <div style={{ color: "var(--sev-critical-text)", padding: "1rem", backgroundColor: "var(--bg-card)" }}>
              ⚠️ {error}
            </div>
          )}

          {detail && !loading && (
            <>
              {/* Triage Action Box */}
              <div className="drawer-section">
                <div className="section-heading">Triage & Investigation Status</div>
                <div className="triage-action-box">
                  <div className="triage-controls-row">
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Status:</span>
                      <select
                        className="filter-select"
                        value={currentStatus}
                        disabled={savingTriage}
                        onChange={(e) => handleStatusChange(e.target.value as TriageStatus)}
                        style={{ fontWeight: 600 }}
                      >
                        <option value="new">New</option>
                        <option value="investigating">Investigating</option>
                        <option value="false_positive">False Positive</option>
                        <option value="resolved">Resolved</option>
                      </select>
                    </div>

                    {savingTriage && (
                      <span style={{ fontSize: "0.75rem", color: "var(--accent-cyan)" }}>
                        ⏳ Saving...
                      </span>
                    )}

                    {triageSuccess && (
                      <span className="saved-indicator">✓ Saved to Database</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Rule & MITRE Metadata */}
              <div className="drawer-section">
                <div className="section-heading">Rule Metadata</div>
                <div
                  style={{
                    backgroundColor: "var(--bg-card)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "1rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.6rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <span className="mono-cell" style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                        Rule ID:{" "}
                      </span>
                      <strong style={{ color: "var(--accent-cyan)" }}>{rule.id}</strong>
                    </div>
                    <SeverityBadge level={rule.level ?? 1} />
                  </div>

                  <div style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>
                    {rule.description}
                  </div>

                  {/* MITRE Mapping */}
                  {(tactics.length > 0 || techIds.length > 0) && (
                    <div style={{ marginTop: "0.4rem" }}>
                      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
                        MITRE ATT&CK:
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
                        {tactics.map((t, idx) => (
                          <span key={`dtactic-${idx}`} className="mitre-badge" style={{ backgroundColor: "var(--bg-app)" }}>
                            🎯 {t}
                          </span>
                        ))}
                        {techIds.map((tId, idx) => (
                          <span
                            key={`dtech-${idx}`}
                            className="mitre-badge"
                            style={{ color: "var(--accent-cyan)", backgroundColor: "var(--bg-app)" }}
                          >
                            🏷️ {tId}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Host & Telemetry Origin */}
              <div className="drawer-section">
                <div className="section-heading">Endpoint / Telemetry Origin</div>
                <div
                  style={{
                    backgroundColor: "var(--bg-card)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "0.85rem 1rem",
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "0.5rem",
                    fontSize: "0.85rem",
                  }}
                >
                  <div>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>Agent Name: </span>
                    <div><strong>{agent.name || "Unknown"}</strong></div>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>IP Address: </span>
                    <div className="mono-cell">{agent.ip || "—"}</div>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>Agent ID: </span>
                    <div className="mono-cell">{agent.id}</div>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>Log Location: </span>
                    <div className="mono-cell" style={{ wordBreak: "break-all" }}>{detail.location || "—"}</div>
                  </div>
                </div>
              </div>

              {/* Raw Log & Payload */}
              <div className="drawer-section">
                <div className="section-heading">Raw Event Telemetry</div>

                {detail.full_log && (
                  <div className="code-block-container" style={{ marginBottom: "0.75rem" }}>
                    <div className="code-block-header">
                      <span>Raw Event Log</span>
                      <button className="btn btn-secondary btn-sm" onClick={handleCopyLog}>
                        {copyLogSuccess ? "✓ Copied" : "📋 Copy Log"}
                      </button>
                    </div>
                    <pre className="code-content">{detail.full_log}</pre>
                  </div>
                )}

                {detail.data && Object.keys(detail.data).length > 0 && (
                  <div className="code-block-container">
                    <div className="code-block-header">
                      <span
                        style={{ cursor: "pointer", userSelect: "none" }}
                        onClick={() => setShowJsonData(!showJsonData)}
                      >
                        {showJsonData ? "▼" : "▶"} Normalized Event Data (JSON)
                      </span>
                      <button className="btn btn-secondary btn-sm" onClick={handleCopyJson}>
                        {copyJsonSuccess ? "✓ Copied" : "📋 Copy JSON"}
                      </button>
                    </div>
                    {showJsonData && (
                      <pre className="code-content">{JSON.stringify(detail.data, null, 2)}</pre>
                    )}
                  </div>
                )}
              </div>

              {/* Analyst Notes */}
              <div className="drawer-section">
                <div className="section-heading">Analyst Investigation Notes ({detail.notes?.length || 0})</div>

                {/* Add Note Form */}
                <form onSubmit={handleAddNote} className="note-input-box">
                  <textarea
                    className="note-textarea"
                    placeholder="Add an investigation note, triage rationale, or IOC comment..."
                    value={noteContent}
                    onChange={(e) => setNoteContent(e.target.value)}
                    disabled={submittingNote}
                  />
                  {noteError && (
                    <div style={{ color: "var(--sev-critical-text)", fontSize: "0.75rem" }}>
                      ⚠️ {noteError}
                    </div>
                  )}
                  <div style={{ display: "flex", justifyContent: "flex-end" }}>
                    <button
                      type="submit"
                      className="btn btn-primary btn-sm"
                      disabled={submittingNote || !noteContent.trim()}
                    >
                      {submittingNote ? "Adding..." : "➕ Add Note"}
                    </button>
                  </div>
                </form>

                {/* Notes List */}
                <div className="notes-container" style={{ marginTop: "0.5rem" }}>
                  {detail.notes && detail.notes.length > 0 ? (
                    detail.notes.map((note) => (
                      <div key={note.id} className="note-card">
                        <div className="note-meta">
                          <span style={{ fontWeight: 600, color: "var(--accent-cyan)" }}>
                            👤 {note.author_id || "Analyst"}
                          </span>
                          <span>{new Date(note.created_at).toLocaleString()}</span>
                        </div>
                        <div style={{ color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>
                          {note.content}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                      No analyst notes added yet.
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
