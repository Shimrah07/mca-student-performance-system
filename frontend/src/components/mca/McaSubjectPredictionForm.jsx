/**
 * frontend/src/components/mca/McaSubjectPredictionForm.jsx
 *
 * Premium Phase 4.8 — Subject prediction form.
 * Zero logic/validation changes — only visual upgrades.
 */

import { useState } from "react";
import { predictSubject } from "../../api/mcaApi";
import McaPredictionResultCard from "./McaPredictionResultCard";

const FIELD_HINT = {
  registration_id:
    "The numeric ID of the MCA course registration record from the database (mca_course_registrations.id).",
  student_id:
    "Optional. The numeric MCA student ID (mca_students.id) for cross-validation.",
  cutoff_timestamp:
    "The snapshot time for feature extraction. The model uses only data recorded before this moment. Required — never inferred automatically.",
};

export default function McaSubjectPredictionForm() {
  const [fields, setFields] = useState({
    registration_id:  "",
    student_id:       "",
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

    const regId = parseInt(fields.registration_id, 10);
    if (!fields.registration_id || isNaN(regId) || regId <= 0) {
      setError("Registration ID must be a positive integer.");
      return;
    }
    if (!fields.cutoff_timestamp) {
      setError("Cutoff timestamp is required. Select the exact snapshot date/time.");
      return;
    }

    const payload = {
      registration_id:  regId,
      cutoff_timestamp: new Date(fields.cutoff_timestamp).toISOString(),
    };

    if (fields.student_id) {
      const sid = parseInt(fields.student_id, 10);
      if (isNaN(sid) || sid <= 0) {
        setError("Student ID must be a positive integer when provided.");
        return;
      }
      payload.student_id = sid;
    }

    setLoading(true);
    try {
      const data = await predictSubject(payload);
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
          <h2 className="card-title">Subject-Level MCA Prediction</h2>
          <p className="card-subtitle">
            Predict a student&apos;s performance tier for a single registered MCA course
            using attendance and formative assessment snapshots.
          </p>
        </div>
      </div>

      {/* DB prerequisite notice */}
      <div className="notice-band">
        ℹ️{" "}
        <strong>Database-Backed Prediction:</strong> Requires verified student registration
        and point-in-time academic snapshots (attendance, formative assessments, or project
        milestones) recorded at or before the cutoff timestamp. Predictions are never
        generated from invented or mock data.
      </div>

      <form onSubmit={handleSubmit}>
        {/* Registration ID */}
        <div className="form-group" style={{ marginBottom: "18px" }}>
          <label className="form-label form-label-required" htmlFor="mca-subj-reg-id">
            Course Registration ID
          </label>
          <input
            id="mca-subj-reg-id"
            type="number"
            min="1"
            className="form-input"
            style={{ maxWidth: "280px" }}
            placeholder="e.g. 1"
            value={fields.registration_id}
            onChange={(e) => setField("registration_id", e.target.value)}
            required
          />
          <span className="form-hint">{FIELD_HINT.registration_id}</span>
        </div>

        {/* Cutoff Timestamp */}
        <div className="form-group" style={{ marginBottom: "18px" }}>
          <label className="form-label form-label-required" htmlFor="mca-subj-cutoff">
            Snapshot Cutoff Date &amp; Time
          </label>
          <input
            id="mca-subj-cutoff"
            type="datetime-local"
            className="form-input"
            style={{ maxWidth: "320px" }}
            value={fields.cutoff_timestamp}
            onChange={(e) => setField("cutoff_timestamp", e.target.value)}
            required
          />
          <span className="form-hint">{FIELD_HINT.cutoff_timestamp}</span>
        </div>

        {/* Student ID (optional) */}
        <div className="form-group" style={{ marginBottom: "22px" }}>
          <label className="form-label" htmlFor="mca-subj-student-id">
            Student ID{" "}
            <span style={{ color: "var(--color-text-secondary)", fontWeight: 400, fontSize: "12px" }}>
              (optional)
            </span>
          </label>
          <input
            id="mca-subj-student-id"
            type="number"
            min="1"
            className="form-input"
            style={{ maxWidth: "280px" }}
            placeholder="e.g. 1"
            value={fields.student_id}
            onChange={(e) => setField("student_id", e.target.value)}
          />
          <span className="form-hint">{FIELD_HINT.student_id}</span>
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
              "🎯 Run Subject Prediction"
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
