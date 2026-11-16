/**
 * frontend/src/components/RecordDetailModal.jsx
 *
 * Detailed inspection modal for a previously persisted prediction record.
 */

function getCategoryColorClass(category) {
  switch (category) {
    case "Excellent":
      return "excellent";
    case "Good":
      return "good";
    case "Average":
      return "average";
    case "Needs Improvement":
    default:
      return "needs-improvement";
  }
}

export default function RecordDetailModal({ record, onClose }) {
  if (!record) return null;

  const colorCls = getCategoryColorClass(record.predicted_category);
  const recs = record.recommendations || {};
  const probs = record.prediction_probabilities || {};

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          className="modal-close-btn"
          onClick={onClose}
          aria-label="Close modal"
        >
          ✕
        </button>

        <div style={{ marginBottom: "16px" }}>
          <span style={{ fontSize: "12px", color: "var(--color-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
            Prediction Record #{record.id}
          </span>
          <h2 style={{ fontSize: "22px", marginTop: "4px" }}>
            Academic Performance Assessment
          </h2>
          <div style={{ fontSize: "13px", color: "var(--color-muted)", marginTop: "4px" }}>
            Generated: {record.created_at ? new Date(record.created_at).toLocaleString() : "Unknown"} ·{" "}
            {record.student_id ? `Linked to Student ID #${record.student_id}` : "Guest Assessment"}
          </div>
        </div>

        {/* Category Result Banner */}
        <div className={`result-header-card ${colorCls}`} style={{ padding: "16px 20px", marginBottom: "18px" }}>
          <div>
            <span className="category-badge-large" style={{ fontSize: "20px", padding: "4px 12px" }}>
              {record.predicted_category}
            </span>
            <div style={{ fontSize: "13px", marginTop: "4px" }}>
              {recs.summary || "Performance estimate based on statistical modeling."}
            </div>
          </div>
        </div>

        {/* Model Meta */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px", marginBottom: "18px", fontSize: "12px", backgroundColor: "#f8fafc", padding: "12px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <div><strong>Subject:</strong> {record.subject}</div>
          <div><strong>Scenario:</strong> {record.scenario}</div>
          <div><strong>Classifier:</strong> {record.model_name}</div>
          <div><strong>Version:</strong> v{record.model_version}</div>
        </div>

        {/* Probability Breakdown */}
        {Object.keys(probs).length > 0 && (
          <div style={{ marginBottom: "20px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: 700, marginBottom: "8px" }}>
              Class Probability Estimates:
            </h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "8px" }}>
              {Object.entries(probs).map(([cat, val]) => (
                <div key={cat} style={{ background: "#f1f5f9", padding: "8px 12px", borderRadius: "6px", fontSize: "12px" }}>
                  <div style={{ fontWeight: 600 }}>{cat}</div>
                  <div style={{ fontSize: "14px", color: "var(--color-primary)", fontWeight: 700 }}>
                    {(val * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actionable recommendations */}
        {recs.actionable_recommendations && recs.actionable_recommendations.length > 0 && (
          <div style={{ marginBottom: "18px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: 700, marginBottom: "8px" }}>
              Recommendations Provided:
            </h4>
            <div className="recs-list" style={{ marginTop: "6px" }}>
              {recs.actionable_recommendations.map((rec, i) => (
                <div key={i} className="rec-item" style={{ padding: "8px 12px" }}>
                  <span className="rec-icon">📌</span>
                  <div style={{ fontSize: "12px" }}>{rec}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Input Feature Snapshot */}
        {record.input_features && (
          <div>
            <h4 style={{ fontSize: "14px", fontWeight: 700, marginBottom: "8px" }}>
              Input Feature Snapshot (Excludes G2 & G3):
            </h4>
            <div style={{ maxHeight: "160px", overflowY: "auto", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "6px", padding: "10px", fontSize: "11px", fontFamily: "var(--font-mono)" }}>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "6px" }}>
                {Object.entries(record.input_features).map(([k, v]) => (
                  <div key={k}>
                    <span style={{ color: "var(--color-muted)" }}>{k}:</span> <strong>{String(v)}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div style={{ marginTop: "20px", display: "flex", justifyContent: "flex-end" }}>
          <button type="button" className="btn-secondary" style={{ color: "var(--color-navy)", borderColor: "#cbd5e1" }} onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
