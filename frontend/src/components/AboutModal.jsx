/**
 * frontend/src/components/AboutModal.jsx
 *
 * Premium Phase 4.8 — Full-page About with elegant typography.
 * Project context, ML methodology, curriculum, ethics.
 */

export default function AboutModal() {
  return (
    <div className="card animate-fade-up">
      <div className="card-header">
        <div>
          <h2 className="card-title">About the Project &amp; Methodology</h2>
          <p className="card-subtitle">
            AI-Based Student Performance Prediction &amp; Academic Support System (MCA)
          </p>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>

        {/* ── Institutional Context ── */}
        <div className="about-section">
          <h3 className="about-section-title">🏛️ Institutional &amp; Programme Context</h3>
          <p style={{ fontSize: "14px", lineHeight: "1.7", color: "var(--color-text-primary)" }}>
            <strong>Master of Computer Applications (MCA) — 3rd Semester Minor Project</strong><br />
            Department of Computer Applications, University Institute of Technology — RGPV
            (Autonomous), Bhopal.<br />
            <span style={{ color: "var(--color-text-secondary)" }}>Academic Session:</span>{" "}
            <strong>2026–27</strong><br />
            <span style={{ color: "var(--color-text-secondary)" }}>Governing Schemes:</span>{" "}
            MCA-AUTONOMOUS-2025 (Sem 1) &amp; MCA-AUTONOMOUS-2024 (Sem 3)<br />
            <span style={{ color: "var(--color-text-secondary)" }}>Curriculum Scope:</span>{" "}
            4 Semesters, 26 Approved Courses — Theory, Practical Lab, Elective Tracks, Minor Project
          </p>
        </div>

        {/* ── Dual-Scope Modeling ── */}
        <div className="about-section">
          <h3 className="about-section-title">🎯 Dual-Scope Performance Modeling</h3>
          <p style={{ fontSize: "14px", lineHeight: "1.7", color: "var(--color-text-secondary)", marginBottom: "14px" }}>
            The system provides two distinct, non-overlapping operational prediction scopes
            designed for early academic intervention.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
            <div
              style={{
                background: "var(--cat-good-bg)",
                border: "1.5px solid var(--cat-good-border)",
                padding: "18px 20px",
                borderRadius: "var(--radius-md)",
              }}
            >
              <div style={{ fontWeight: 700, color: "var(--cat-good-text)", marginBottom: "8px", fontSize: "14px" }}>
                1 · Subject-Level Prediction
              </div>
              <div style={{ fontSize: "13px", lineHeight: "1.6", color: "var(--color-text-secondary)" }}>
                Evaluates a single registered course using point-in-time attendance
                percentage, formative assessments (MST-1, MST-2, assignments, lab records,
                vivas), and milestone reviews. Powered by a trained{" "}
                <strong>Logistic Regression</strong> pipeline (macro-F1: 0.6732).
              </div>
            </div>

            <div
              style={{
                background: "#F3EDFF",
                border: "1.5px solid #C9B8E8",
                padding: "18px 20px",
                borderRadius: "var(--radius-md)",
              }}
            >
              <div style={{ fontWeight: 700, color: "#5C3A8C", marginBottom: "8px", fontSize: "14px" }}>
                2 · Semester-Level Prediction
              </div>
              <div style={{ fontSize: "13px", lineHeight: "1.6", color: "var(--color-text-secondary)" }}>
                Aggregates academic features across all active course registrations in the
                target semester and incorporates finalized prior-semester SGPA/CGPA records.
                Powered by a trained{" "}
                <strong>Random Forest</strong> pipeline (macro-F1: 0.6973).
              </div>
            </div>
          </div>
        </div>

        {/* ── 4-Tier Mapping ── */}
        <div className="about-section">
          <h3 className="about-section-title">📊 4-Tier Performance Trajectory</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px", marginTop: "10px" }}>
            {[
              {
                tier: "Excellent",
                desc: "High academic distinction; consistent attendance and top formative scores.",
                bg: "var(--cat-excellent-bg)", border: "var(--cat-excellent-border)", text: "var(--cat-excellent-text)",
              },
              {
                tier: "Good",
                desc: "Solid foundational performance meeting all curriculum expectations.",
                bg: "var(--cat-good-bg)", border: "var(--cat-good-border)", text: "var(--cat-good-text)",
              },
              {
                tier: "Average",
                desc: "Passing competency; targeted formative support recommended to prevent drop-off.",
                bg: "var(--cat-average-bg)", border: "var(--cat-average-border)", text: "var(--cat-average-text)",
              },
              {
                tier: "Needs Improvement",
                desc: "Early-warning alert; prioritized for remedial mentoring and attendance recovery.",
                bg: "var(--cat-needs-bg)", border: "var(--cat-needs-border)", text: "var(--cat-needs-text)",
              },
            ].map(({ tier, desc, bg, border, text }) => (
              <div
                key={tier}
                style={{ background: bg, border: `1.5px solid ${border}`, padding: "14px", borderRadius: "var(--radius-md)" }}
              >
                <strong style={{ color: text, fontSize: "13.5px" }}>{tier}</strong>
                <div style={{ fontSize: "12px", color: text, marginTop: "5px", lineHeight: "1.5", opacity: 0.85 }}>
                  {desc}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Temporal Integrity ── */}
        <div className="about-section">
          <h3 className="about-section-title">⏱️ Point-in-Time Temporal Cutoff Enforcement</h3>
          <p style={{ fontSize: "14px", lineHeight: "1.7", color: "var(--color-text-primary)" }}>
            To guarantee strict data-leakage protection, all feature extraction queries enforce
            a caller-specified{" "}
            <code>cutoff_timestamp</code>. Any assessment score, attendance entry, or result
            declared after this timestamp is barred from the model input vector.
            Target-semester final exam grades are strictly excluded.
          </p>
        </div>

        {/* ── Tech Stack ── */}
        <div className="about-section">
          <h3 className="about-section-title">🔧 Technology Stack</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "10px", fontSize: "13px" }}>
            {[
              ["Backend",    "FastAPI + Python 3.14, SQLAlchemy (ORM)"],
              ["Database",   "MySQL 8 (mca_academic_system)"],
              ["ML Models",  "scikit-learn · Logistic Regression · Random Forest"],
              ["Frontend",   "React 19 + Vite — no UI framework"],
              ["Data",       "Synthetic MCA dataset (Phase 3A)"],
              ["Hosting",    "Localhost prototype — not production deployed"],
            ].map(([k, v]) => (
              <div
                key={k}
                style={{ background: "var(--color-sage)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)", padding: "12px 14px" }}
              >
                <div style={{ fontWeight: 700, color: "var(--color-text-primary)", marginBottom: "3px" }}>{k}</div>
                <div style={{ color: "var(--color-text-secondary)", lineHeight: "1.5" }}>{v}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Synthetic Notice ── */}
        <div style={{ background: "#FFF8E6", border: "1.5px solid #F0D49A", borderRadius: "var(--radius-md)", padding: "18px 20px" }}>
          <h4 style={{ fontSize: "14.5px", fontWeight: 700, marginBottom: "6px", color: "#6B4A0E", display: "flex", alignItems: "center", gap: "7px" }}>
            ⚠️ Academic Integrity &amp; Synthetic Dataset Notice
          </h4>
          <p style={{ margin: 0, fontSize: "13px", lineHeight: "1.65", color: "#6B4A0E" }}>
            The machine learning models used in this prototype were trained exclusively on
            synthetic MCA datasets (6,370 subject-level records and 1,200 semester-level
            records) specifically synthesized to mirror UIT-RGPV curriculum distributions.
            They do <strong>not</strong> contain real student records. Predictions generated by
            this system are academic prototype demonstrations and must not be used for actual
            university grading or disciplinary actions.
          </p>
        </div>

      </div>
    </div>
  );
}
