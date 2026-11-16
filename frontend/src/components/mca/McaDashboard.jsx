/**
 * frontend/src/components/mca/McaDashboard.jsx
 *
 * Top-level MCA section with internal sub-tab navigation:
 *   Overview | Curriculum | Subject Prediction | Semester Prediction | History
 */

import { useState } from "react";
import McaCurriculumBrowser from "./McaCurriculumBrowser";
import McaSubjectPredictionForm from "./McaSubjectPredictionForm";
import McaSemesterPredictionForm from "./McaSemesterPredictionForm";
import McaPredictionHistoryPanel from "./McaPredictionHistoryPanel";

const TABS = [
  { id: "overview", label: "🏠 Overview" },
  { id: "curriculum", label: "📚 Curriculum" },
  { id: "subject", label: "🎯 Subject Prediction" },
  { id: "semester", label: "📊 Semester Prediction" },
  { id: "history", label: "📋 History" },
];

function OverviewPanel() {
  return (
    <div>
      {/* Hero */}
      <section className="hero-card" style={{ marginBottom: "24px" }}>
        <span className="hero-tag">MCA · Prototype Prediction System · Synthetic Dataset</span>
        <h1 className="hero-title" style={{ fontSize: "26px" }}>
          MCA Student Performance Prediction
        </h1>
        <p className="hero-desc" style={{ fontSize: "14px" }}>
          An MCA-specific machine learning pipeline trained on synthetic student data for
          UIT-RGPV (Autonomous). Predicts performance tiers — <strong>Excellent</strong>,{" "}
          <strong>Good</strong>, <strong>Average</strong>, <strong>Needs Improvement</strong> —
          at subject and semester level.
        </p>
        <div
          style={{
            background: "rgba(252,211,77,0.15)",
            border: "1px solid rgba(252,211,77,0.5)",
            borderRadius: "8px",
            padding: "10px 16px",
            fontSize: "13px",
            color: "#fef9c3",
            marginTop: "12px",
            maxWidth: "720px",
          }}
        >
          ⚠️ <strong>Prototype Notice:</strong> All predictions use models trained on
          <em> synthetic</em> MCA data, not real UIT-RGPV academic records. Results are
          illustrative only and must not be used for real academic decisions.
        </div>
      </section>

      {/* Architecture Cards */}
      <section className="features-grid">
        <div className="feature-box">
          <div className="feature-icon-wrapper">🤖</div>
          <div className="feature-box-title">Dual ML Models</div>
          <div className="feature-box-desc">
            Subject-level: <strong>Logistic Regression</strong> (macro-F1 ≈ 0.67) ·
            Semester-level: <strong>Random Forest</strong> (macro-F1 ≈ 0.70). Both trained on
            MCA-specific synthetic features.
          </div>
        </div>
        <div className="feature-box">
          <div className="feature-icon-wrapper">📋</div>
          <div className="feature-box-title">26-Course Curriculum</div>
          <div className="feature-box-desc">
            Full 4-semester MCA curriculum with Semester 1 fully code-verified (MCA108–MCA114),
            Semester 3 confirmed (MCA301–MCA307), and Semesters 2 &amp; 4 syllabus-confirmed.
          </div>
        </div>
        <div className="feature-box">
          <div className="feature-icon-wrapper">🗄️</div>
          <div className="feature-box-title">13-Table Architecture</div>
          <div className="feature-box-desc">
            MCA-specific SQLAlchemy ORM with programs, curriculum schemes, courses, academic
            sessions, students, registrations, and prediction persistence.
          </div>
        </div>
        <div className="feature-box">
          <div className="feature-icon-wrapper">⚡</div>
          <div className="feature-box-title">FastAPI Backend</div>
          <div className="feature-box-desc">
            8 MCA endpoints: curriculum browsing, subject prediction, semester prediction, and
            prediction history retrieval. Served at <code>localhost:8000</code>.
          </div>
        </div>
      </section>

      {/* Endpoint Reference */}
      <div className="card" style={{ marginTop: "24px" }}>
        <h3 style={{ fontSize: "15px", fontWeight: 700, marginBottom: "14px" }}>
          🔌 Available API Endpoints
        </h3>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ textAlign: "left" }}>Method</th>
                <th style={{ textAlign: "left" }}>Endpoint</th>
                <th style={{ textAlign: "left" }}>Description</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["GET", "/health", "Backend health check"],
                ["GET", "/health/db", "MySQL connectivity check"],
                ["GET", "/api/mca/curriculum", "Full 4-semester curriculum"],
                ["GET", "/api/mca/semesters/{n}", "Single semester courses"],
                ["POST", "/api/mca/predictions/subject", "Subject-level prediction"],
                ["POST", "/api/mca/predictions/semester", "Semester-level prediction"],
                ["GET", "/api/mca/predictions/{id}", "Retrieve saved prediction"],
                ["GET", "/api/mca/predictions/student/{id}", "Student prediction history"],
              ].map(([method, path, desc]) => (
                <tr key={path}>
                  <td>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        padding: "2px 7px",
                        borderRadius: "4px",
                        background: method === "POST" ? "#faf5ff" : "#eff6ff",
                        color: method === "POST" ? "#7e22ce" : "#1d4ed8",
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      {method}
                    </span>
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "13px" }}>{path}</td>
                  <td style={{ fontSize: "13px", color: "var(--color-muted)" }}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default function McaDashboard() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div>
      {/* Sub-nav */}
      <div
        style={{
          display: "flex",
          gap: "4px",
          borderBottom: "2px solid var(--color-border)",
          marginBottom: "24px",
          overflowX: "auto",
          paddingBottom: "0",
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "10px 16px",
              fontSize: "13px",
              fontWeight: 600,
              border: "none",
              background: "none",
              cursor: "pointer",
              color: activeTab === tab.id ? "var(--color-primary)" : "var(--color-muted)",
              borderBottom: activeTab === tab.id ? "2px solid var(--color-primary)" : "2px solid transparent",
              marginBottom: "-2px",
              whiteSpace: "nowrap",
              transition: "color 0.15s",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Panel */}
      {activeTab === "overview" && <OverviewPanel />}
      {activeTab === "curriculum" && <McaCurriculumBrowser />}
      {activeTab === "subject" && <McaSubjectPredictionForm />}
      {activeTab === "semester" && <McaSemesterPredictionForm />}
      {activeTab === "history" && <McaPredictionHistoryPanel />}
    </div>
  );
}
