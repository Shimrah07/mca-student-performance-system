/**
 * frontend/src/components/mca/McaPredictionHistoryPanel.jsx
 *
 * Premium Phase 4.8 — MCA prediction history with refined table, scope/tier badges.
 * Zero logic changes — only visual upgrades.
 */

import { useState } from "react";
import { getStudentPredictions } from "../../api/mcaApi";
import McaPredictionResultCard from "./McaPredictionResultCard";

function TierBadge({ tier }) {
  const cls = {
    "Excellent":         "excellent",
    "Good":              "good",
    "Average":           "average",
    "Needs Improvement": "needs-improvement",
  }[tier] || "";
  return <span className={`badge ${cls}`}>{tier}</span>;
}

function ScopeBadge({ scope }) {
  const cls = scope === "semester" ? "scope-semester" : "scope-subject";
  return <span className={`scope-badge ${cls}`}>{scope}</span>;
}

export default function McaPredictionHistoryPanel() {
  const [studentId, setStudentId] = useState("");
  const [limit,     setLimit]     = useState(20);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState(null);
  const [records,   setRecords]   = useState(null);
  const [expanded,  setExpanded]  = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    setError(null);
    setRecords(null);
    setExpanded(null);

    const sid = parseInt(studentId, 10);
    if (!studentId || isNaN(sid) || sid <= 0) {
      setError("Please enter a valid positive student ID.");
      return;
    }

    setLoading(true);
    try {
      const data = await getStudentPredictions(sid, limit);
      setRecords(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load prediction history.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card animate-fade-up">
      <div className="card-header">
        <div>
          <h2 className="card-title">MCA Prediction History</h2>
          <p className="card-subtitle">
            Retrieve saved predictions for a specific MCA student from the database.
          </p>
        </div>
      </div>

      {/* ── Search Bar ── */}
      <form
        onSubmit={handleSearch}
        style={{ display: "flex", gap: "14px", alignItems: "flex-end", flexWrap: "wrap", marginBottom: "22px" }}
      >
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label form-label-required" htmlFor="mca-hist-sid">
            Student ID
          </label>
          <input
            id="mca-hist-sid"
            type="number"
            min="1"
            className="form-input"
            style={{ maxWidth: "180px" }}
            placeholder="e.g. 1"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            required
          />
        </div>

        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label" htmlFor="mca-hist-limit">
            Max Results
          </label>
          <select
            id="mca-hist-limit"
            className="form-select"
            style={{ maxWidth: "120px" }}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
          >
            {[10, 20, 50].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <button type="submit" className="btn-primary" disabled={loading} style={{ marginBottom: 0 }}>
          {loading ? <><span className="spinner" /> Loading…</> : "🔍 Load History"}
        </button>
      </form>

      {/* ── Error ── */}
      {error && (
        <div className="alert-box alert-error" role="alert">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* ── Empty State ── */}
      {records !== null && records.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-icon">📂</div>
          <h3 style={{ fontSize: "16px", fontWeight: 700, marginBottom: "6px" }}>No predictions found</h3>
          <p style={{ fontSize: "13px", color: "var(--color-text-secondary)" }}>
            No saved predictions for student #{studentId}. Run a subject or semester assessment first.
          </p>
        </div>
      )}

      {/* ── Results Table ── */}
      {records && records.length > 0 && (
        <>
          <div style={{ fontSize: "13px", color: "var(--color-text-secondary)", marginBottom: "14px" }}>
            Showing <strong style={{ color: "var(--color-text-primary)" }}>{records.length}</strong> record{records.length !== 1 ? "s" : ""} for student #{studentId}
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Scope</th>
                  <th style={{ textAlign: "left" }}>Course / Semester</th>
                  <th>Tier</th>
                  <th>Confidence</th>
                  <th>Model</th>
                  <th>Date</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {records.map((rec) => (
                  <>
                    <tr key={rec.prediction_id}>
                      <td>
                        <span style={{ fontWeight: 700, color: "var(--color-forest)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
                          #{rec.prediction_id}
                        </span>
                      </td>
                      <td><ScopeBadge scope={rec.scope} /></td>
                      <td style={{ textAlign: "left" }}>
                        {rec.course_name
                          ? `${rec.course_code ? rec.course_code + " — " : ""}${rec.course_name}`
                          : rec.target_semester
                          ? `Semester ${rec.target_semester}`
                          : "—"}
                      </td>
                      <td><TierBadge tier={rec.predicted_tier} /></td>
                      <td style={{ fontWeight: 600 }}>
                        {rec.confidence != null ? `${Math.round(rec.confidence * 100)}%` : "—"}
                      </td>
                      <td style={{ fontSize: "11.5px", color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>
                        {rec.model_name}
                      </td>
                      <td style={{ fontSize: "12.5px" }}>
                        {rec.created_at ? new Date(rec.created_at).toLocaleDateString() : "—"}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn-view-record"
                          onClick={() => setExpanded(expanded === rec.prediction_id ? null : rec.prediction_id)}
                        >
                          {expanded === rec.prediction_id ? "Hide" : "Expand"}
                        </button>
                      </td>
                    </tr>

                    {expanded === rec.prediction_id && (
                      <tr key={`${rec.prediction_id}-detail`}>
                        <td colSpan={8} style={{ padding: "0 16px 18px", borderBottom: "none" }}>
                          <McaPredictionResultCard result={rec} onClose={() => setExpanded(null)} />
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
