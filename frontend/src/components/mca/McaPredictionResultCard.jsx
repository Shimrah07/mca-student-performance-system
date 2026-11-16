/**
 * frontend/src/components/mca/McaPredictionResultCard.jsx
 *
 * Premium Phase 4.8 — Renders a single MCA prediction response from the backend.
 * Shows: tier badge, confidence, animated probability bars, metadata grid, disclaimer.
 * Zero API-contract changes.
 */

const TIER_STYLES = {
  Excellent:          { bg: "var(--cat-excellent-bg)", border: "var(--cat-excellent-border)", text: "var(--cat-excellent-text)", bar: "var(--cat-excellent-bar)", cls: "excellent" },
  Good:               { bg: "var(--cat-good-bg)",      border: "var(--cat-good-border)",      text: "var(--cat-good-text)",      bar: "var(--cat-good-bar)",      cls: "good" },
  Average:            { bg: "var(--cat-average-bg)",   border: "var(--cat-average-border)",   text: "var(--cat-average-text)",   bar: "var(--cat-average-bar)",   cls: "average" },
  "Needs Improvement":{ bg: "var(--cat-needs-bg)",     border: "var(--cat-needs-border)",     text: "var(--cat-needs-text)",     bar: "var(--cat-needs-bar)",     cls: "needs-improvement" },
};

const TIER_ORDER = ["Excellent", "Good", "Average", "Needs Improvement"];

function ConfidenceDisplay({ value }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div style={{ textAlign: "center", flexShrink: 0 }}>
      <div
        style={{
          fontSize: "42px",
          fontWeight: 800,
          color: "var(--color-text-primary)",
          lineHeight: 1,
          letterSpacing: "-0.04em",
          fontFamily: "var(--font-display)",
        }}
      >
        {pct}<span style={{ fontSize: "22px" }}>%</span>
      </div>
      <div style={{ fontSize: "11px", color: "var(--color-text-secondary)", marginTop: "5px", textTransform: "uppercase", letterSpacing: "0.07em", fontWeight: 500 }}>
        Model Confidence
      </div>
    </div>
  );
}

export default function McaPredictionResultCard({ result, onClose }) {
  if (!result) return null;

  const tier       = result.predicted_tier || "Unknown";
  const tierStyle  = TIER_STYLES[tier] || { bg: "var(--color-sage)", border: "var(--color-border)", text: "var(--color-text-primary)", bar: "var(--color-green-muted)", cls: "" };
  const probs      = result.probabilities || {};
  const isSynth    = result.synthetic_data_warning !== false;

  const scopeLabel = result.scope === "semester" ? "Semester-Level Prediction" : "Subject-Level Prediction";

  return (
    <div
      className="animate-fade-up"
      style={{
        border: `1.5px solid ${tierStyle.border}`,
        borderRadius: "var(--radius-lg)",
        background: tierStyle.bg,
        padding: "26px",
        marginTop: "22px",
      }}
    >
      {/* ── Tier Header Row ── */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "20px",
          flexWrap: "wrap",
          marginBottom: "22px",
        }}
      >
        <div>
          <div
            style={{
              fontSize: "11px",
              fontWeight: 700,
              color: tierStyle.text,
              textTransform: "uppercase",
              letterSpacing: "0.09em",
              marginBottom: "8px",
              opacity: 0.78,
            }}
          >
            {scopeLabel}
          </div>

          <div
            className="category-badge-large"
            style={{ color: tierStyle.text, background: "rgba(255,255,255,0.80)", border: `1px solid ${tierStyle.border}` }}
          >
            {tier}
          </div>

          {result.course_name && (
            <div style={{ marginTop: "10px", fontSize: "13.5px", color: "var(--color-text-primary)", fontWeight: 500 }}>
              <span style={{ color: "var(--color-text-secondary)", fontWeight: 400 }}>Course: </span>
              {result.course_code ? `${result.course_code} — ` : ""}{result.course_name}
            </div>
          )}
          {result.target_semester && (
            <div style={{ fontSize: "13.5px", color: "var(--color-text-primary)", fontWeight: 500, marginTop: "4px" }}>
              <span style={{ color: "var(--color-text-secondary)", fontWeight: 400 }}>Semester: </span>
              {result.target_semester}
            </div>
          )}
        </div>

        <ConfidenceDisplay value={result.confidence} />
      </div>

      {/* ── Probability Bars ── */}
      {Object.keys(probs).length > 0 && (
        <div
          style={{
            background: "rgba(255,255,255,0.65)",
            border: `1px solid ${tierStyle.border}`,
            borderRadius: "var(--radius-md)",
            padding: "18px 20px",
            marginBottom: "18px",
          }}
        >
          <div
            style={{
              fontSize: "11px",
              fontWeight: 700,
              color: "var(--color-text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.07em",
              marginBottom: "14px",
            }}
          >
            Probability Distribution
          </div>

          {TIER_ORDER.map((t) => {
            const val = probs[t] ?? 0;
            const s   = TIER_STYLES[t] || { bar: "var(--color-green-muted)", cls: "" };
            const pct = Math.min(100, Math.max(val * 100, 0));
            return (
              <div key={t} style={{ marginBottom: "12px" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "13px",
                    marginBottom: "5px",
                    fontWeight: 600,
                    color: "var(--color-text-primary)",
                  }}
                >
                  <span>{t}</span>
                  <span style={{ color: s.bar }}>{(val * 100).toFixed(1)}%</span>
                </div>
                <div className="prob-bar-container">
                  <div
                    className={`prob-bar-fill ${s.cls}`}
                    style={{ width: `${Math.max(pct, 1.5)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Metadata Grid ── */}
      <div className="meta-grid">
        {[
          { label: "Prediction ID",  value: result.prediction_id ? `#${result.prediction_id} · Persisted` : "—" },
          { label: "Model",          value: result.model_name ?? "—" },
          { label: "Version",        value: result.model_version ?? "—" },
          { label: "Student ID",     value: result.student_id ?? "—" },
          { label: "Cutoff",         value: result.cutoff_timestamp ? new Date(result.cutoff_timestamp).toLocaleString() : "—" },
        ].map(({ label, value }) => (
          <div key={label} className="meta-cell">
            <div className="meta-cell-label">{label}</div>
            <div className="meta-cell-value">{String(value)}</div>
          </div>
        ))}
      </div>

      {/* ── Synthetic Data Disclaimer ── */}
      {isSynth && (
        <div className="disclaimer-banner">
          ⚠️{" "}
          <strong>Prototype Notice:</strong> This prediction was generated by a model trained
          on synthetic MCA data, not real UIT-RGPV academic records. Results are for
          demonstration purposes only and must not be used for university grading or
          disciplinary actions.
        </div>
      )}

      {onClose && (
        <div style={{ textAlign: "right", marginTop: "16px" }}>
          <button type="button" className="btn-secondary" onClick={onClose}
            style={{ background: "rgba(255,255,255,0.65)", border: `1px solid ${tierStyle.border}`, color: tierStyle.text }}
          >
            ✕ Close
          </button>
        </div>
      )}
    </div>
  );
}
