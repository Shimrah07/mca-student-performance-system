/**
 * frontend/src/components/mca/McaSemesterPredictionForm.jsx
 *
 * Premium Phase 4.8 — Semester prediction form.
 * Zero logic/validation changes — only visual upgrades.
 */

import { useState } from "react";
import { predictSemester } from "../../api/mcaApi";
import McaPredictionResultCard from "./McaPredictionResultCard";

const SEMESTER_OPTIONS = [1, 2, 3, 4];

export default function McaSemesterPredictionForm() {
  const [fields, setFields] = useState({
    student_id:       "",
    target_semester:  "1",
    cutoff_timestamp: "",
  });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);
  const [result,  setResult]  = useState(null);

  const setField = (name, value) => setFields((f) => ({ ...f, [name]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    const sid = parseInt(fields.student_id, 10);
    if (!fields.student_id || isNaN(sid) || sid <= 0) {
      setError("Student ID must be a positive integer.");
      return;
    }

    const sem = parseInt(fields.target_semester, 10);
    if (isNaN(sem) || sem < 1 || sem > 4) {
      setError("Target semester must be between 1 and 4.");
      return;
    }

    if (!fields.cutoff_timestamp) {
      setError("Cutoff timestamp is required. Select the exact snapshot date/time.");
      return;
    }

    const payload = {
      student_id:       sid,
      target_semester:  sem,
      cutoff_timestamp: new Date(fields.cutoff_timestamp).toISOString(),
    };

    setLoading(true);
    try {
      const data = await predictSemester(payload);
      setResult(data);
    } catch (err) {
      setError(err.message || "Prediction request failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card animate-fade-up">
      <div className="card-header">
        <div>
          <h2 className="card-title">Semester-Level MCA Prediction</h2>
          <p className="card-subtitle">
            Predict a student&apos;s overall semester performance tier by aggregating all
            course registrations and academic snapshots up to the cutoff date.
          </p>
        </div>
      </div>

      {/* DB prerequisite notice */}
      <div className="notice-band">
        ℹ️{" "}
        <strong>Database-Backed Prediction:</strong> Requires active course registrations and
        point-in-time academic snapshots across enrolled courses recorded at or before the
        cutoff timestamp. Predictions are never generated from invented or mock data.
      </div>

      <form onSubmit={handleSubmit}>
        {/* Student ID */}
        <div className="form-group" style={{ marginBottom: "18px" }}>
          <label className="form-label form-label-required" htmlFor="mca-sem-student-id">
            Student ID
          </label>
          <input
            id="mca-sem-student-id"
            type="number"
            min="1"
            className="form-input"
            style={{ maxWidth: "280px" }}
            placeholder="e.g. 1"
            value={fields.student_id}
            onChange={(e) => setField("student_id", e.target.value)}
            required
          />
          <span className="form-hint">Numeric MCA student ID from mca_students table.</span>
        </div>

        {/* Target Semester — pill selector */}
        <div className="form-group" style={{ marginBottom: "18px" }}>
          <label className="form-label form-label-required" htmlFor="mca-sem-target">
            Target Semester
          </label>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "2px" }}>
            {SEMESTER_OPTIONS.map((n) => {
              const active = fields.target_semester === String(n);
              return (
                <button
                  key={n}
                  type="button"
                  onClick={() => setField("target_semester", String(n))}
                  style={{
                    padding: "7px 20px",
                    borderRadius: "var(--radius-full)",
                    fontSize: "13.5px",
                    fontWeight: active ? 700 : 500,
                    border: active ? "1.5px solid var(--color-forest)" : "1.5px solid var(--color-border)",
                    background: active ? "var(--color-forest)" : "var(--color-surface)",
                    color: active ? "#fff" : "var(--color-text-secondary)",
                    cursor: "pointer",
                    transition: "all 150ms ease",
                    fontFamily: "var(--font-sans)",
                  }}
                >
                  Sem {n}
                </button>
              );
            })}
          </div>
          {/* Hidden native select for form value */}
          <input type="hidden" name="target_semester" value={fields.target_semester} />
          <span className="form-hint">
            The MCA semester (1–4) for which the prediction should be generated.
          </span>
        </div>

        {/* Cutoff Timestamp */}
        <div className="form-group" style={{ marginBottom: "22px" }}>
          <label className="form-label form-label-required" htmlFor="mca-sem-cutoff">
            Snapshot Cutoff Date &amp; Time
          </label>
          <input
            id="mca-sem-cutoff"
            type="datetime-local"
            className="form-input"
            style={{ maxWidth: "320px" }}
            value={fields.cutoff_timestamp}
            onChange={(e) => setField("cutoff_timestamp", e.target.value)}
            required
          />
          <span className="form-hint">
            The model uses only academic snapshots recorded before this timestamp. Never
            auto-filled — explicit entry required.
          </span>
        </div>

        {error && (
          <div className="alert-box alert-error" role="alert">
            <strong>Error:</strong> {error}
          </div>
        )}

        <div className="form-submit-bar">
          <span style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>
            🔒 Prototype model — trained on synthetic MCA dataset, not real student records.
          </span>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (
              <><span className="spinner" /> Predicting…</>
            ) : (
              "📊 Run Semester Prediction"
            )}
          </button>
        </div>
      </form>

      {result && (
        <McaPredictionResultCard result={result} onClose={() => setResult(null)} />
      )}
    </div>
  );
}
