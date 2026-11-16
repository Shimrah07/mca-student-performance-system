/**
 * frontend/src/components/mca/McaOverview.jsx
 *
 * Dashboard view inspired by the reference SaaS visual design:
 * - Bold header with clean subtitle
 * - Signature 4-card metric row (Deep forest-green hero card + 3 white metric cards with diagonal arrows)
 * - Trajectory distribution widget & quick intervention action cards
 * - 4 core architectural pillar cards
 * - Clean REST API catalog table
 * - Synthetic data notice
 */

import {
  ArrowUpRightIcon,
  SubjectIcon,
  SemesterIcon,
  CurriculumIcon,
  HistoryIcon,
} from "../common/Icons";

export default function McaOverview({ onNavigate }) {
  return (
    <div className="animate-fade-up">
      {/* ── Dashboard Page Header ── */}
      <div className="dashboard-header">
        <div>
          <h1 className="dashboard-title">Dashboard</h1>
          <p className="dashboard-subtitle">
            Plan, monitor, &amp; predict MCA student academic trajectories with point-in-time intelligence
          </p>
        </div>

        <div className="dashboard-header-badge">
          <span className="badge-tag">UIT-RGPV Autonomous</span>
          <span className="badge-session">Session 2026–27</span>
        </div>
      </div>

      {/* ── Metric Cards Row (Directly inspired by reference image) ── */}
      <div className="metrics-grid">
        {/* Card 1: Deep Forest Green Hero Card */}
        <div className="metric-card metric-card-forest" onClick={() => onNavigate("curriculum")}>
          <div className="metric-header">
            <span className="metric-label">Target Curriculum</span>
            <span className="metric-arrow-btn">
              <ArrowUpRightIcon size={16} />
            </span>
          </div>
          <div className="metric-number">4</div>
          <div className="metric-footer">
            <span className="metric-sub-pill">26 Approved Courses · Sem 1 to 4</span>
          </div>
        </div>

        {/* Card 2: White Card */}
        <div className="metric-card" onClick={() => onNavigate("curriculum")}>
          <div className="metric-header">
            <span className="metric-label">Curriculum Schemes</span>
            <span className="metric-arrow-btn">
              <ArrowUpRightIcon size={16} />
            </span>
          </div>
          <div className="metric-number">2</div>
          <div className="metric-footer">
            <span className="metric-sub-text">Autonomous 2024 &amp; 2025 Schemes</span>
          </div>
        </div>

        {/* Card 3: White Card */}
        <div className="metric-card" onClick={() => onNavigate("subject")}>
          <div className="metric-header">
            <span className="metric-label">Active ML Models</span>
            <span className="metric-arrow-btn">
              <ArrowUpRightIcon size={16} />
            </span>
          </div>
          <div className="metric-number">2</div>
          <div className="metric-footer">
            <span className="metric-sub-text">Logistic Reg &amp; Random Forest</span>
          </div>
        </div>

        {/* Card 4: White Card */}
        <div className="metric-card" onClick={() => onNavigate("semester")}>
          <div className="metric-header">
            <span className="metric-label">Performance Tiers</span>
            <span className="metric-arrow-btn">
              <ArrowUpRightIcon size={16} />
            </span>
          </div>
          <div className="metric-number">4</div>
          <div className="metric-footer">
            <span className="metric-sub-text">Excellent · Good · Avg · Needs Imp.</span>
          </div>
        </div>
      </div>

      {/* ── Middle Split Row: Visual Trajectory & Quick Assessment Actions ── */}
      <div className="dashboard-split-grid">
        {/* Left: Performance Trajectory Visualizer */}
        <div className="card dashboard-widget">
          <div className="card-header-clean">
            <div>
              <h2 className="widget-title">Performance Trajectory Tiers</h2>
              <p className="widget-subtitle">Four-tier early classification calibrated to UIT-RGPV grading</p>
            </div>
            <span className="widget-header-arrow">
              <ArrowUpRightIcon size={16} />
            </span>
          </div>

          <div className="trajectory-bars-container">
            <div className="trajectory-col">
              <div className="trajectory-pill-bar pill-excellent" />
              <span className="trajectory-col-label">Excellent</span>
              <span className="trajectory-col-sub">&ge; 8.5 CGPA</span>
            </div>
            <div className="trajectory-col">
              <div className="trajectory-pill-bar pill-good" />
              <span className="trajectory-col-label">Good</span>
              <span className="trajectory-col-sub">7.0–8.4 CGPA</span>
            </div>
            <div className="trajectory-col">
              <div className="trajectory-pill-bar pill-average" />
              <span className="trajectory-col-label">Average</span>
              <span className="trajectory-col-sub">5.5–6.9 CGPA</span>
            </div>
            <div className="trajectory-col">
              <div className="trajectory-pill-bar pill-needs" />
              <span className="trajectory-col-label">Needs Imp.</span>
              <span className="trajectory-col-sub">&lt; 5.5 CGPA</span>
            </div>
          </div>

          <div className="trajectory-info-strip">
            <span>🛡️ <strong>Zero Data Leakage:</strong> Temporal cutoffs strictly bar future attendance and final marks.</span>
          </div>
        </div>

        {/* Right: Quick Action Launchpad */}
        <div className="card dashboard-widget">
          <div className="card-header-clean">
            <div>
              <h2 className="widget-title">Quick Action Launchpad</h2>
              <p className="widget-subtitle">Trigger point-in-time performance evaluations</p>
            </div>
          </div>

          <div className="quick-actions-list">
            <button
              type="button"
              className="quick-action-item"
              onClick={() => onNavigate("subject")}
            >
              <div className="action-item-icon icon-subject">
                <SubjectIcon size={20} />
              </div>
              <div className="action-item-content">
                <div className="action-item-title">Subject Assessment</div>
                <div className="action-item-desc">Predict single course performance via attendance &amp; MSTs</div>
              </div>
              <ArrowUpRightIcon size={15} className="action-item-arrow" />
            </button>

            <button
              type="button"
              className="quick-action-item"
              onClick={() => onNavigate("semester")}
            >
              <div className="action-item-icon icon-semester">
                <SemesterIcon size={20} />
              </div>
              <div className="action-item-content">
                <div className="action-item-title">Semester Assessment</div>
                <div className="action-item-desc">Aggregate semester outcome across all active registrations</div>
              </div>
              <ArrowUpRightIcon size={15} className="action-item-arrow" />
            </button>

            <button
              type="button"
              className="quick-action-item"
              onClick={() => onNavigate("history")}
            >
              <div className="action-item-icon icon-history">
                <HistoryIcon size={20} />
              </div>
              <div className="action-item-content">
                <div className="action-item-title">Prediction History</div>
                <div className="action-item-desc">Query verified immutable prediction records by Student ID</div>
              </div>
              <ArrowUpRightIcon size={15} className="action-item-arrow" />
            </button>

            <button
              type="button"
              className="quick-action-item"
              onClick={() => onNavigate("curriculum")}
            >
              <div className="action-item-icon icon-curriculum">
                <CurriculumIcon size={20} />
              </div>
              <div className="action-item-content">
                <div className="action-item-title">Browse Curriculum</div>
                <div className="action-item-desc">Inspect all 26 official theory, lab, and project courses</div>
              </div>
              <ArrowUpRightIcon size={15} className="action-item-arrow" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Architectural Highlights ── */}
      <div className="features-grid">
        <div className="feature-box">
          <div className="feature-box-badge">Phase 3A Verified</div>
          <div className="feature-box-title">Dual Machine Learning Pipelines</div>
          <div className="feature-box-desc">
            Subject-level Logistic Regression (macro-F1: 0.6732) and Semester-level Random Forest (macro-F1: 0.6973), trained without diagnostic bias.
          </div>
        </div>

        <div className="feature-box">
          <div className="feature-box-badge">UIT-RGPV Schemes</div>
          <div className="feature-box-title">26-Course Canonical Curriculum</div>
          <div className="feature-box-desc">
            Governed by official Autonomous schemes (July 2025 &amp; July 2024). Verified course codes (MCA108–114, MCA301–307) with theory, lab, and project tracks.
          </div>
        </div>

        <div className="feature-box">
          <div className="feature-box-badge">Deterministic Cutoff</div>
          <div className="feature-box-title">Point-in-Time Temporal Extraction</div>
          <div className="feature-box-desc">
            Phase 2E temporal barrier enforcement. Snapshots recorded after the explicit cutoff date are strictly excluded. Missing data is never fabricated.
          </div>
        </div>

        <div className="feature-box">
          <div className="feature-box-badge">Audit Integrity</div>
          <div className="feature-box-title">Immutable Audit Persistence</div>
          <div className="feature-box-desc">
            Append-only audit trail in <code>mca_prediction_records</code>. Every prediction stores an immutable snapshot of features, version, and probabilities.
          </div>
        </div>
      </div>

      {/* ── API Endpoint Catalog ── */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">MCA REST API Endpoint Catalog</h2>
            <p className="card-subtitle">
              FastAPI backend integration running at <code>http://localhost:8000</code>
            </p>
          </div>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Scope</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["GET", "/health", "System", "API operational readiness check"],
                ["GET", "/health/db", "System", "Safe MySQL connectivity check with masked credentials"],
                ["GET", "/api/mca/curriculum", "Curriculum", "Full 4-semester curriculum (26 courses)"],
                ["GET", "/api/mca/semesters/{n}", "Curriculum", "Single-semester course roster (n: 1–4)"],
                ["POST", "/api/mca/predictions/subject", "Inference", "Point-in-time subject prediction &amp; audit persistence"],
                ["POST", "/api/mca/predictions/semester", "Inference", "Point-in-time semester prediction &amp; audit persistence"],
                ["GET", "/api/mca/predictions/{id}", "Audit", "Retrieve immutable prediction audit record by ID"],
                ["GET", "/api/mca/predictions/student/{id}", "Audit", "List historical predictions for an MCA student"],
              ].map(([method, path, scope, desc]) => (
                <tr key={path}>
                  <td>
                    <span className={`method-badge method-${method.toLowerCase()}`}>
                      {method}
                    </span>
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "12.5px" }}>{path}</td>
                  <td>
                    <span style={{ fontSize: "12px", color: "var(--color-text-secondary)", fontWeight: 600 }}>
                      {scope}
                    </span>
                  </td>
                  <td style={{ fontSize: "13px", color: "var(--color-text-secondary)" }}
                    dangerouslySetInnerHTML={{ __html: desc }}
                  />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Prototype Notice Banner ── */}
      <div className="notice-banner-amber">
        <div className="notice-banner-icon">⚠️</div>
        <div className="notice-banner-content">
          <strong>Academic Prototype &amp; Synthetic Dataset Notice:</strong> The ML classification
          pipelines were trained on synthetic MCA data calibrated to UIT-RGPV academic distributions (Phase 3A).
          They do not contain real student identities. Predictions require explicit database records and point-in-time
          cutoff timestamps.
        </div>
      </div>
    </div>
  );
}
