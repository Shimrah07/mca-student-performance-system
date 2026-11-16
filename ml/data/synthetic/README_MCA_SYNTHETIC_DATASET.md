# MCA Academic Performance — Synthetic Prototype Dataset

## Important limitation
This is **synthetic/artificially generated data**. It is not UIT-RGPV student data, not collected from real students, and not evidence of real-world model accuracy. Use it only for development, pipeline testing, demonstrations, and learning. Do not present its evaluation metrics as real academic prediction performance.

## Files
- `mca_synthetic_subject_level.csv`: one row per synthetic student-course registration (6,370 rows).
- `mca_synthetic_semester_level.csv`: one row per synthetic student-semester (1,200 rows).

## Data generation
- Random seed: `20261113` (reproducible).
- Synthetic students: 1,200.
- Subject-level rows: 6,370.
- Semester-level rows: 1,200.
- Course catalogue: the approved 26-course MCA catalogue, with verified codes only for Semesters 1 and 3.
- Allowed course types: `theory`, `lab`, `elective`, `project`.
- No names, phone numbers, addresses, or other personal identifiers are included.

## Prediction targets
- `performance_tier`: target class: `Excellent`, `Good`, `Average`, `Needs Improvement`.
- `synthetic_final_score` / `synthetic_semester_final_score`: **target-only outcome columns**. They must never be included as model input features.
- Prototype-only score bands used to generate labels:
  - Excellent: score >= 80
  - Good: 65 <= score < 80
  - Average: 50 <= score < 65
  - Needs Improvement: score < 50

These are engineering/demo thresholds only. They are **not official UIT-RGPV grading rules** and must be configurable/replaced when verified institutional outcome definitions are available.

## Feature columns
Subject-level records contain:
- Identity/context: `record_id`, pseudonymous `student_id`, synthetic `registration_id`, `semester_number`, `course_code`, `course_title`, `course_type`, `prediction_scope`, `cutoff_timestamp`.
- Theory/elective: `attendance_percentage`, `mst1_marks`, `mst2_marks`, `assignment_marks`.
- Lab: `practical_attendance_percentage`, `experiments_completed`, `experiments_total`, `viva_marks`, `lab_journal_marks`.
- Project: `synopsis_approved`, `literature_survey_completed`, `design_approved`, `implementation_percentage`, `faculty_guide_interaction_score`.
- Shared: `study_hours_per_week`, `prior_sgpa`, `prior_cgpa`, `math_background_score`.
- Some feature values are intentionally missing to exercise missing-data handling. Semester 1 prior SGPA/CGPA are NULL because no earlier semester is represented.

Semester-level records contain means of available subject-level feature values, course counts and course-type metadata. They are aggregated synthetic examples, not direct outputs from the application's production feature-extraction service.

## Critical ML safeguards
1. Exclude `synthetic_final_score`, `synthetic_semester_final_score`, `performance_tier`, `record_id`, `registration_id`, and student identifiers from X (model inputs).
2. Use `performance_tier` as y for classification, or use the synthetic score as a separate regression target, never as an input.
3. Split by `student_id` (group-based train/test split) so records for the same synthetic student do not appear in both training and test sets.
4. Fit imputers, encoders, scalers and feature selection only on training folds (use an sklearn Pipeline).
5. Report macro-F1, per-class precision/recall, confusion matrix and class distribution. Accuracy alone is insufficient.
6. Do not claim the synthetic test score estimates performance on real MCA students.
7. Keep subject-level and semester-level models/datasets separate unless a justified, tested design supports combining them.
8. For deployment, the model must accept the same feature schema as the application's point-in-time feature extractor. Map columns explicitly; do not silently substitute unrelated or unavailable features.
9. Do not use future or target-semester final results as input features. Respect the application's exact cutoff rules.

## Class counts
Subject-level: {"Excellent": 1900, "Average": 1540, "Needs Improvement": 1514, "Good": 1416}
Semester-level: {"Good": 464, "Average": 335, "Excellent": 229, "Needs Improvement": 172}

## Compatibility note
This is a development dataset designed around the approved academic feature categories. Antigravity must inspect the actual output schema of `mca_feature_extraction.py` and create an explicit, tested mapping/adapter. Do not change the approved ORM schema just to force a match.
