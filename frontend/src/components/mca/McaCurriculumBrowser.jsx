/**
 * frontend/src/components/mca/McaCurriculumBrowser.jsx
 *
 * Full 4-semester MCA curriculum browser with clean white panels,
 * subtle borders, and clear course typography.
 */

import { useEffect, useState } from "react";
import { getCurriculum } from "../../api/mcaApi";
import { MCA_SEMESTERS } from "../../constants/mcaCurriculum";

function CourseTypeBadge({ type }) {
  const cls = {
    theory:   "course-type-theory",
    lab:      "course-type-lab",
    elective: "course-type-elective",
    project:  "course-type-project",
  }[type] || "";

  const label = {
    theory:   "Theory",
    lab:      "Lab",
    elective: "Elective",
    project:  "Project",
  }[type] || type;

  return (
    <span className={`course-type-badge ${cls}`}>{label}</span>
  );
}

function SemesterPanel({ semester }) {
  const courses      = semester.subjects || semester.courses || [];
  const totalCredits = courses.reduce((s, c) => s + (c.credits || 0), 0);

  return (
    <div className="semester-panel">
      <div className="semester-panel-header">
        <div>
          <div className="semester-panel-title">Semester {semester.semester_number}</div>
          {semester.academic_focus && (
            <div className="semester-panel-focus">{semester.academic_focus}</div>
          )}
        </div>
        <div className="semester-panel-stats">
          <div>
            <strong style={{ color: "var(--color-text-primary)" }}>{courses.length}</strong> courses
          </div>
          {totalCredits > 0 && (
            <div>
              <strong style={{ color: "var(--color-text-primary)" }}>{totalCredits}</strong> credits
            </div>
          )}
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table className="course-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Course Name</th>
              <th>Type</th>
              <th>Credits</th>
            </tr>
          </thead>
          <tbody>
            {courses.map((course, idx) => (
              <tr key={course.id || course.course_code || idx}>
                <td>
                  <span className="course-code">
                    {course.code || course.course_code || "—"}
                  </span>
                </td>
                <td>
                  <span className="course-name">
                    {course.name || course.course_name}
                    {course.elective_group && (
                      <span
                        style={{
                          marginLeft: "8px",
                          fontSize: "10.5px",
                          color: "#5C3A8C",
                          fontWeight: 600,
                          background: "#F3EDFF",
                          padding: "1px 7px",
                          borderRadius: "9999px",
                        }}
                      >
                        {course.elective_group}
                      </span>
                    )}
                  </span>
                </td>
                <td><CourseTypeBadge type={course.course_type} /></td>
                <td style={{ fontWeight: 700, color: "var(--color-text-primary)" }}>
                  {course.credits != null ? course.credits : (
                    <span style={{ color: "var(--color-text-secondary)", fontStyle: "italic", fontWeight: 400 }}>TBC</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function McaCurriculumBrowser() {
  const [semesters, setSemesters] = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [source,    setSource]    = useState("api");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getCurriculum();
        if (!cancelled) {
          setSemesters(data.semesters || data);
          setSource("api");
        }
      } catch {
        if (!cancelled) {
          setSemesters(MCA_SEMESTERS);
          setSource("local");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="animate-fade-up">
      <div className="curriculum-header">
        <div>
          <h2 className="page-title">MCA Curriculum Schemes</h2>
          <p className="page-subtitle">
            UIT-RGPV (Autonomous) · Master of Computer Applications · 4 Semesters · 26 Courses
          </p>
        </div>
        <span className={`source-badge ${source === "api" ? "live" : "offline"}`}>
          {source === "api" ? "✓ Live from API" : "⚠ Offline — local data"}
        </span>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: "64px", color: "var(--color-text-secondary)" }}>
          <span className="spinner" />
          <p style={{ marginTop: "14px" }}>Loading curriculum from backend…</p>
        </div>
      ) : (
        <>
          {(semesters || []).map((sem) => (
            <SemesterPanel key={sem.semester_number} semester={sem} />
          ))}

          <div
            style={{
              fontSize: "12px",
              color: "var(--color-text-secondary)",
              borderTop: "1px solid var(--color-border)",
              paddingTop: "14px",
              marginTop: "6px",
            }}
          >
            ⓘ Courses with code "—" or credits "TBC" are syllabus-confirmed but pending
            official scheme publication. No data is invented.
          </div>
        </>
      )}
    </div>
  );
}
