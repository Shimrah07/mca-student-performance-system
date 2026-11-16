/**
 * frontend/src/components/PredictionResults.jsx
 *
 * Displays predicted performance tier, indicative probabilities breakdown,
 * identified strengths, actionable recommendations, and pedagogical disclaimers.
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

export default function PredictionResults({ result, onReset, onViewHistory }) {
  if (!result) return null;

  const colorClass = getCategoryColorClass(result.predicted_category);
  const probabilities = result.prediction_probabilities || {};

  // Ordered performance tiers for probability visualization
  const orderedTiers = [
    { key: "Excellent", label: "Excellent (16–20 Distinction)", cls: "excellent" },
    { key: "Good", label: "Good (14–15 Good Standing)", cls: "good" },
    { key: "Average", label: "Average (10–13 Passing)", cls: "average" },
    { key: "Needs Improvement", label: "Needs Improvement (0–9 Below Pass)", cls: "needs-improvement" },
  ];

  return (
    <div>
      {/* 1. Header Banner */}
      <div className={`result-header-card ${colorClass}`}>
        <div>
          <span className="category-badge-large">
            {result.predicted_category}
          </span>
          <p className="category-summary-text">{result.summary}</p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "8px", alignItems: "flex-end" }}>
          <div className="model-meta-badge">
            <span>Subject:</span> <strong>{result.subject}</strong>
            <span>|</span>
            <span>Scenario:</span> <strong>{result.scenario}</strong>
          </div>
          <div className="model-meta-badge">
            <span>Model:</span> <strong>{result.model_name} (v{result.model_version})</strong>
          </div>
          <div className="model-meta-badge" style={{ backgroundColor: result.persisted ? "#ecfdf5" : "#f1f5f9" }}>
            <span>Status:</span>{" "}
            <strong>
              {result.persisted
                ? `✓ Saved to History (ID: #${result.prediction_id})`
                : "ℹ Guest Mode (Not Saved to DB)"}
            </strong>
          </div>
        </div>
      </div>

      {/* 2. Class Probabilities Distribution */}
      {Object.keys(probabilities).length > 0 && (
        <div className="prob-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "16px" }}>
            <h3 style={{ fontSize: "16px", fontWeight: 700 }}>
              📊 Indicative Class Probability Distribution
            </h3>
            <span style={{ fontSize: "11px", color: "var(--color-muted)" }}>
              Model-Estimated Confidence Across 4 Tiers
            </span>
          </div>

          <div>
            {orderedTiers.map((tier) => {
              const val = probabilities[tier.key] !== undefined ? probabilities[tier.key] : 0;
              const percentage = Math.round(val * 100);

              return (
                <div key={tier.key} className="prob-row">
                  <div className="prob-label-row">
                    <span>{tier.label}</span>
                    <span>
                      {(val * 100).toFixed(1)}% ({val.toFixed(4)})
                    </span>
                  </div>
                  <div className="prob-bar-container">
                    <div
                      className={`prob-bar-fill ${tier.cls}`}
                      style={{ width: `${Math.max(percentage, 2)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: "12px", fontSize: "11px", color: "var(--color-muted)", fontStyle: "italic" }}>
            {result.probabilities_note ||
              "Indicative model estimates only. Probabilities are uncalibrated and do not represent guaranteed real-world risk."}
          </div>
        </div>
      )}

      {/* 3. Actionable Recommendations & Strengths Grid */}
      <div className="results-columns">
        {/* Actionable Recommendations */}
        <div className="recs-card">
          <h3 style={{ fontSize: "16px", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
            <span>💡</span> Actionable Recommendations
          </h3>
          <p style={{ fontSize: "12px", color: "var(--color-muted)", marginTop: "2px" }}>
            Rule-based suggestions tailored to student habits and identified risk factors:
          </p>

          <div className="recs-list">
            {result.actionable_recommendations && result.actionable_recommendations.length > 0 ? (
              result.actionable_recommendations.map((rec, idx) => (
                <div key={idx} className="rec-item">
                  <span className="rec-icon">📌</span>
                  <div>{rec}</div>
                </div>
              ))
            ) : (
              <div className="rec-item">
                <span className="rec-icon">✔️</span>
                <div>Maintain regular study schedules and consult instructors as needed.</div>
              </div>
            )}
          </div>
        </div>

        {/* Strengths Identified */}
        <div className="recs-card">
          <h3 style={{ fontSize: "16px", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
            <span>🌟</span> Identified Strengths & Positive Factors
          </h3>
          <p style={{ fontSize: "12px", color: "var(--color-muted)", marginTop: "2px" }}>
            Positive academic and behavioral commitments recognized by the system:
          </p>

          <div className="recs-list">
            {result.strengths_identified && result.strengths_identified.length > 0 ? (
              result.strengths_identified.map((str, idx) => (
                <div key={idx} className="strength-item">
                  <span style={{ fontSize: "16px" }}>✅</span>
                  <div>{str}</div>
                </div>
              ))
            ) : (
              <div style={{ fontSize: "13px", color: "var(--color-muted)", padding: "12px" }}>
                Steady baseline indicators noted across evaluated areas.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Evaluated Factors Snapshot */}
      {result.evaluated_factors && Object.keys(result.evaluated_factors).length > 0 && (
        <div className="card">
          <h4 style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-slate)" }}>
            Factors Evaluated for Specific Guidance:
          </h4>
          <div className="factors-wrap">
            {Object.entries(result.evaluated_factors).map(([key, val]) => (
              <span key={key} className="factor-tag">
                {key}: <strong>{String(val)}</strong>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 5. Pedagogical Disclaimer Banner */}
      <div className="disclaimer-banner">
        <strong>⚖️ Safety & Pedagogical Notice:</strong> {result.disclaimer}
      </div>

      {/* 6. Action Bar */}
      <div style={{ display: "flex", gap: "14px", marginTop: "24px", justifyContent: "flex-end" }}>
        <button
          type="button"
          className="btn-secondary"
          style={{ color: "var(--color-navy)", borderColor: "var(--color-border)" }}
          onClick={onViewHistory}
        >
          📋 View Prediction History
        </button>
        <button
          type="button"
          className="btn-primary"
          onClick={onReset}
        >
          🔄 Start Another Assessment
        </button>
      </div>
    </div>
  );
}
