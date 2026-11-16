/**
 * frontend/src/components/PredictionForm.jsx
 *
 * Comprehensive student information input form.
 * Enforces scenario requirements (Scenario A vs. Scenario B), validated boundaries,
 * and strict data leakage exclusion (never collects G2 or G3).
 */

import { useState } from "react";
import {
  SUBJECT_OPTIONS,
  SCENARIO_OPTIONS,
  SCHOOL_OPTIONS,
  SEX_OPTIONS,
  ADDRESS_OPTIONS,
  FAMSIZE_OPTIONS,
  PSTATUS_OPTIONS,
  JOB_OPTIONS,
  REASON_OPTIONS,
  GUARDIAN_OPTIONS,
  EDU_LEVEL_OPTIONS,
  TRAVELTIME_OPTIONS,
  STUDYTIME_OPTIONS,
  FAILURES_OPTIONS,
  SCALE_1_TO_5,
  YES_NO_OPTIONS,
  SAMPLE_PROFILES,
} from "../constants/formOptions";
import { predictStudentPerformance } from "../api/client";

const INITIAL_FEATURES = {
  // Binary features (13)
  school: "GP",
  sex: "F",
  address: "U",
  famsize: "GT3",
  Pstatus: "T",
  schoolsup: "no",
  famsup: "yes",
  paid: "no",
  activities: "yes",
  nursery: "yes",
  higher: "yes",
  internet: "yes",
  romantic: "no",

  // Categorical nominal (4)
  Mjob: "other",
  Fjob: "other",
  reason: "course",
  guardian: "mother",

  // Ordinal survey attributes (11)
  Medu: 2,
  Fedu: 2,
  traveltime: 1,
  studytime: 2,
  failures: 0,
  famrel: 4,
  freetime: 3,
  goout: 3,
  Dalc: 1,
  Walc: 1,
  health: 3,

  // Continuous/count attributes (2)
  age: 16,
  absences: 2,

  // First-period grade (Scenario B only)
  G1: 12,
};

export default function PredictionForm({ onPredictionSuccess }) {
  const [subject, setSubject] = useState("Mathematics");
  const [scenario, setScenario] = useState("Scenario A");
  const [studentCode, setStudentCode] = useState("");
  const [features, setFeatures] = useState(INITIAL_FEATURES);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Field change handler
  const handleFeatureChange = (name, value, isNumeric = false) => {
    setFeatures((prev) => ({
      ...prev,
      [name]: isNumeric ? Number(value) : value,
    }));
  };

  // Prefill helper
  const handleLoadSample = (sampleKey) => {
    const sample = SAMPLE_PROFILES[sampleKey];
    if (sample) {
      setSubject(sample.subject);
      setScenario(sample.scenario);
      setStudentCode(sample.student_code || "");
      setFeatures({ ...INITIAL_FEATURES, ...sample.features });
      setError(null);
    }
  };

  const handleReset = () => {
    setSubject("Mathematics");
    setScenario("Scenario A");
    setStudentCode("");
    setFeatures(INITIAL_FEATURES);
    setError(null);
  };

  // Form submission handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Build clean features payload strictly excluding G2, G3, and excluding G1 in Scenario A
      const payloadFeatures = { ...features };

      if (scenario === "Scenario A") {
        delete payloadFeatures.G1;
      } else {
        // Enforce G1 is numeric and valid for Scenario B
        if (payloadFeatures.G1 === undefined || payloadFeatures.G1 === null || payloadFeatures.G1 === "") {
          throw new Error("Scenario B requires a valid First-Period Grade (G1) between 0 and 20.");
        }
        payloadFeatures.G1 = Number(payloadFeatures.G1);
        if (payloadFeatures.G1 < 0 || payloadFeatures.G1 > 20) {
          throw new Error("First-Period Grade (G1) must be between 0 and 20.");
        }
      }

      // Explicit safeguard: ensure leakage fields are never attached
      delete payloadFeatures.G2;
      delete payloadFeatures.G3;

      const payload = {
        subject,
        scenario,
        features: payloadFeatures,
        student_code: studentCode.trim() ? studentCode.trim() : null,
      };

      const result = await predictStudentPerformance(payload);
      onPredictionSuccess(result);
    } catch (err) {
      setError(err.message || "Failed to generate prediction. Please check inputs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Student Academic Assessment Form</h2>
          <p className="card-subtitle">
            Configure assessment parameters and enter student profile data.
          </p>
        </div>
      </div>

      {/* Prefill Demonstration Strip */}
      <div className="prefill-strip">
        <span className="prefill-label">Quick Demonstration Profiles:</span>
        <button
          type="button"
          className="btn-sample"
          onClick={() => handleLoadSample("high_achiever")}
        >
          🌟 High Achiever (Scenario A)
        </button>
        <button
          type="button"
          className="btn-sample"
          onClick={() => handleLoadSample("needs_support")}
        >
          ⚠️ At-Risk Student (Scenario A)
        </button>
        <button
          type="button"
          className="btn-sample"
          onClick={() => handleLoadSample("midterm_diagnostic")}
        >
          📊 Mid-Term with G1 (Scenario B)
        </button>
        <button
          type="button"
          className="btn-sample"
          onClick={handleReset}
        >
          🔄 Reset Form
        </button>
      </div>

      {error && (
        <div className="alert-box alert-error" role="alert">
          <strong>Validation / Server Error:</strong> {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Core Configuration Row */}
        <div className="form-config-row">
          <div className="form-group">
            <label className="form-label form-label-required" htmlFor="select-subject">
              Subject Evaluated
            </label>
            <select
              id="select-subject"
              className="form-select"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            >
              {SUBJECT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <span className="form-hint">
              Select Mathematics or Portuguese Language pipeline.
            </span>
          </div>

          <div className="form-group">
            <label className="form-label form-label-required" htmlFor="select-scenario">
              Prediction Scenario
            </label>
            <select
              id="select-scenario"
              className="form-select"
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
            >
              {SCENARIO_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <span className="form-hint">
              {scenario === "Scenario A"
                ? "Scenario A: 30 non-grade factors. No exam marks required."
                : "Scenario B: 31 factors including First-Period Exam Grade (G1)."}
            </span>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="input-student-code">
              Student Identifier (Optional)
            </label>
            <input
              id="input-student-code"
              type="text"
              className="form-input"
              placeholder="e.g. STU-2026-001 (or leave blank for guest)"
              value={studentCode}
              onChange={(e) => setStudentCode(e.target.value)}
            />
            <span className="form-hint">
              Anonymized code to link prediction history.
            </span>
          </div>
        </div>

        {/* Highlighted G1 input block for Scenario B */}
        {scenario === "Scenario B" && (
          <div className="g1-highlight-box">
            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="input-g1">
                First-Period Exam Grade (G1) [0 to 20 Scale]
              </label>
              <input
                id="input-g1"
                type="number"
                min="0"
                max="20"
                step="0.5"
                className="form-input"
                style={{ maxWidth: "200px" }}
                value={features.G1 ?? ""}
                onChange={(e) => handleFeatureChange("G1", e.target.value, true)}
                required
              />
              <span className="form-hint" style={{ color: "#1e40af" }}>
                Period 1 assessment mark (Passing mark in Portuguese grading is 10/20).
                Required for Scenario B mid-term diagnostic.
              </span>
            </div>
          </div>
        )}

        {/* Section 1: School & Demographics */}
        <div className="form-section">
          <div className="form-section-title">
            <span>🏫</span> Section 1: School & Personal Demographics
          </div>
          <div className="form-section-desc">
            Baseline enrollment characteristics and household arrangements.
          </div>

          <div className="form-grid-3">
            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-school">School</label>
              <select
                id="field-school"
                className="form-select"
                value={features.school}
                onChange={(e) => handleFeatureChange("school", e.target.value)}
              >
                {SCHOOL_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-sex">Gender</label>
              <select
                id="field-sex"
                className="form-select"
                value={features.sex}
                onChange={(e) => handleFeatureChange("sex", e.target.value)}
              >
                {SEX_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-age">Age (15–22)</label>
              <input
                id="field-age"
                type="number"
                min="15"
                max="22"
                className="form-input"
                value={features.age}
                onChange={(e) => handleFeatureChange("age", e.target.value, true)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-address">Home Location</label>
              <select
                id="field-address"
                className="form-select"
                value={features.address}
                onChange={(e) => handleFeatureChange("address", e.target.value)}
              >
                {ADDRESS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-famsize">Family Size</label>
              <select
                id="field-famsize"
                className="form-select"
                value={features.famsize}
                onChange={(e) => handleFeatureChange("famsize", e.target.value)}
              >
                {FAMSIZE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-Pstatus">Parent Cohabitation</label>
              <select
                id="field-Pstatus"
                className="form-select"
                value={features.Pstatus}
                onChange={(e) => handleFeatureChange("Pstatus", e.target.value)}
              >
                {PSTATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Section 2: Family Background & Support */}
        <div className="form-section">
          <div className="form-section-title">
            <span>👨‍👩‍👧</span> Section 2: Family Background & Support
          </div>
          <div className="form-section-desc">
            Parental educational attainment, professions, and academic support channels.
          </div>

          <div className="form-grid-3">
            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-Medu">Mother's Education</label>
              <select
                id="field-Medu"
                className="form-select"
                value={features.Medu}
                onChange={(e) => handleFeatureChange("Medu", e.target.value, true)}
              >
                {EDU_LEVEL_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-Fedu">Father's Education</label>
              <select
                id="field-Fedu"
                className="form-select"
                value={features.Fedu}
                onChange={(e) => handleFeatureChange("Fedu", e.target.value, true)}
              >
                {EDU_LEVEL_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-Mjob">Mother's Job</label>
              <select
                id="field-Mjob"
                className="form-select"
                value={features.Mjob}
                onChange={(e) => handleFeatureChange("Mjob", e.target.value)}
              >
                {JOB_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-Fjob">Father's Job</label>
              <select
                id="field-Fjob"
                className="form-select"
                value={features.Fjob}
                onChange={(e) => handleFeatureChange("Fjob", e.target.value)}
              >
                {JOB_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-reason">School Selection Reason</label>
              <select
                id="field-reason"
                className="form-select"
                value={features.reason}
                onChange={(e) => handleFeatureChange("reason", e.target.value)}
              >
                {REASON_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-guardian">Primary Guardian</label>
              <select
                id="field-guardian"
                className="form-select"
                value={features.guardian}
                onChange={(e) => handleFeatureChange("guardian", e.target.value)}
              >
                {GUARDIAN_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-schoolsup">School Educational Support</label>
              <select
                id="field-schoolsup"
                className="form-select"
                value={features.schoolsup}
                onChange={(e) => handleFeatureChange("schoolsup", e.target.value)}
              >
                {YES_NO_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-famsup">Family Educational Support</label>
              <select
                id="field-famsup"
                className="form-select"
                value={features.famsup}
                onChange={(e) => handleFeatureChange("famsup", e.target.value)}
              >
                {YES_NO_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-paid">Extra Paid Classes</label>
              <select
                id="field-paid"
                className="form-select"
                value={features.paid}
                onChange={(e) => handleFeatureChange("paid", e.target.value)}
              >
                {YES_NO_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Section 3: Study Habits & History */}
        <div className="form-section">
          <div className="form-section-title">
            <span>📚</span> Section 3: Study Habits & Academic History
          </div>
          <div className="form-section-desc">
            Independent revision time, commute duration, and prior subject performance.
          </div>

          <div className="form-grid-3">
            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-studytime">Weekly Study Time</label>
              <select
                id="field-studytime"
                className="form-select"
                value={features.studytime}
                onChange={(e) => handleFeatureChange("studytime", e.target.value, true)}
              >
                {STUDYTIME_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-traveltime">Travel Time to School</label>
              <select
                id="field-traveltime"
                className="form-select"
                value={features.traveltime}
                onChange={(e) => handleFeatureChange("traveltime", e.target.value, true)}
              >
                {TRAVELTIME_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-failures">Past Class Failures</label>
              <select
                id="field-failures"
                className="form-select"
                value={features.failures}
                onChange={(e) => handleFeatureChange("failures", e.target.value, true)}
              >
                {FAILURES_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-higher">Higher Education Aspiration</label>
              <select
                id="field-higher"
                className="form-select"
                value={features.higher}
                onChange={(e) => handleFeatureChange("higher", e.target.value)}
              >
                {YES_NO_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-activities">Extra-curricular Activities</label>
              <select
                id="field-activities"
                className="form-select"
                value={features.activities}
                onChange={(e) => handleFeatureChange("activities", e.target.value)}
              >
                {YES_NO_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-nursery">Attended Nursery School</label>
              <select
                id="field-nursery"
                className="form-select"
                value={features.nursery}
                onChange={(e) => handleFeatureChange("nursery", e.target.value)}
              >
                {YES_NO_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-internet">Internet Access at Home</label>
              <select
                id="field-internet"
                className="form-select"
                value={features.internet}
                onChange={(e) => handleFeatureChange("internet", e.target.value)}
              >
                {YES_NO_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-romantic">Romantic Relationship</label>
              <select
                id="field-romantic"
                className="form-select"
                value={features.romantic}
                onChange={(e) => handleFeatureChange("romantic", e.target.value)}
              >
                {YES_NO_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Section 4: Lifestyle, Health & Attendance */}
        <div className="form-section">
          <div className="form-section-title">
            <span>🌿</span> Section 4: Lifestyle, Well-Being & Attendance
          </div>
          <div className="form-section-desc">
            Social engagement, self-reported health, and school absenteeism.
          </div>

          <div className="form-grid-3">
            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-absences">School Absences (0–93)</label>
              <input
                id="field-absences"
                type="number"
                min="0"
                max="93"
                className="form-input"
                value={features.absences}
                onChange={(e) => handleFeatureChange("absences", e.target.value, true)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-famrel">Family Relationships</label>
              <select
                id="field-famrel"
                className="form-select"
                value={features.famrel}
                onChange={(e) => handleFeatureChange("famrel", e.target.value, true)}
              >
                {SCALE_1_TO_5.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-freetime">Free Time After School</label>
              <select
                id="field-freetime"
                className="form-select"
                value={features.freetime}
                onChange={(e) => handleFeatureChange("freetime", e.target.value, true)}
              >
                {SCALE_1_TO_5.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-goout">Going Out with Friends</label>
              <select
                id="field-goout"
                className="form-select"
                value={features.goout}
                onChange={(e) => handleFeatureChange("goout", e.target.value, true)}
              >
                {SCALE_1_TO_5.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-Dalc">Workday Alcohol Consumption</label>
              <select
                id="field-Dalc"
                className="form-select"
                value={features.Dalc}
                onChange={(e) => handleFeatureChange("Dalc", e.target.value, true)}
              >
                {SCALE_1_TO_5.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-Walc">Weekend Alcohol Consumption</label>
              <select
                id="field-Walc"
                className="form-select"
                value={features.Walc}
                onChange={(e) => handleFeatureChange("Walc", e.target.value, true)}
              >
                {SCALE_1_TO_5.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label form-label-required" htmlFor="field-health">Current Health Status</label>
              <select
                id="field-health"
                className="form-select"
                value={features.health}
                onChange={(e) => handleFeatureChange("health", e.target.value, true)}
              >
                {SCALE_1_TO_5.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Error Alert Bar near submit button */}
        {error && (
          <div className="alert-box alert-error" role="alert" style={{ marginTop: "16px", marginBottom: "16px" }}>
            <strong>Assessment Error:</strong> {error}
          </div>
        )}

        {/* Submit Bar */}
        <div className="form-submit-bar">
          <div style={{ fontSize: "12px", color: "var(--color-muted)" }}>
            🔒 Strict data leakage controls active. Future marks (G2, G3) are never requested or evaluated.
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" /> Generating Prediction...
              </>
            ) : (
              "🚀 Run Performance Prediction"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
