# Machine Learning Methodology & Evaluation

**Academic Context:** MCA 3rd Semester Minor Project, UIT-RGPV (Autonomous), Bhopal  
**Phase:** Phase 3A (Model Training) & Phase 3B (Inference Integration)  
**Dataset Nature:** Calibrated Synthetic MCA Dataset (Strictly Non-Institutional)  

---

## 1. Dual Machine Learning Pipeline Architecture

The application implements two distinct, specialized machine learning classification pipelines targeting different decision-support levels in the academic lifecycle:

| Specification | Subject-Level Pipeline | Semester-Level Pipeline |
|---|---|---|
| **Operational Target** | Individual Course Tier Forecasting | Holistic Semester Trajectory Forecasting |
| **Model Algorithm** | Multinomial Logistic Regression (`L-BFGS`) | Random Forest Classifier (`n_estimators=100`) |
| **Input Feature Count** | 14 features (13 numeric, 1 categorical) | 8 features (all numeric) |
| **Target Variable** | `subject_performance_tier` (4 classes) | `semester_performance_tier` (4 classes) |
| **Synthetic Dataset Size**| 6,370 course-level rows | 1,200 semester-level rows |
| **Unique Synthetic Students** | 1,200 students | 1,200 students |
| **Test Accuracy (Synthetic)** | **69.10%** | **70.42%** |
| **Macro F1-Score (Synthetic)** | **0.6732** | **0.6973** |

---

## 2. Performance Tier Categorization

Target variables are mapped to four intuitive, actionable academic support categories reflecting UIT-RGPV grading conventions:

```
┌────────────────────┬──────────────┬────────────────────────────────────────────────────────┐
│ Performance Tier   │ Equivalent   │ Recommended Intervention & Support Strategy            │
├────────────────────┼──────────────┼────────────────────────────────────────────────────────┤
│ Excellent          │ ≥ 8.5 CGPA   │ Advanced enrichment tracks, honors research, mentoring │
│ Good               │ 7.0–8.4 CGPA │ Standard curriculum progression; elective guidance     │
│ Average            │ 5.5–6.9 CGPA │ Targeted tutorial sessions; continuous assessment watch│
│ Needs Improvement  │ < 5.5 CGPA   │ Early remedial intervention; mandatory attendance catch│
└────────────────────┴──────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. Synthetic Dataset Generation & Distribution

Because institutional student records are protected by academic privacy laws and lack standardized historical snapshot tracking at the minor project phase, a calibrated synthetic dataset was constructed (Phase 3A):
- **Calibrated Distributions**: Generated using realistic multivariate normal and beta distributions calibrated against official UIT-RGPV examination grading profiles.
- **Grouped Student Cohorts**: Multiple course records belong to individual synthetic students across semesters to mirror real registration structures.
- **Synthetic Isolation**: Synthetic candidate codes (`MCA-SYNTH-XXXX`) and artificial test identifiers are strictly excluded from model feature sets.

---

## 4. Strict Data Leakage Prevention Guarantees

In educational data mining, data leakage frequently inflates laboratory model accuracy at the expense of real-world utility. This project enforces three rigorous anti-leakage barriers:

1. **Temporal Cutoff Boundary**: Every feature extraction request requires an explicit `cutoff_timestamp`. Any snapshot recorded or finalized after this moment is strictly excluded:
   $$\text{Eligible Snapshots} = \{s \in S \mid \text{recorded\_at}(s) \le t_{\text{cutoff}}\}$$
2. **Exclusion of Target-Semester Exam Marks**: The final examination marks (end-semester theory/practical) for the evaluated semester are never accessible to the feature extractor.
3. **No Target-Derived Features**: Features such as total semester marks, SGPA of the current semester, or grade point outputs are completely barred. Only historical previous-semester SGPA/CGPA ($\text{sem} < \text{target\_sem}$) are eligible.
4. **Group-Based Train/Test Splitting**: The synthetic dataset was split using `GroupKFold` / `GroupShuffleSplit` on `student_id` (80% train, 20% test). No student appeared in both training and test sets.

---

## 5. Feature Engineering & Preprocessing

### 5.1 Subject-Level Features (14)
- **Categorical (1)**:
  - `course_type`: Course pedagogical classification (`theory`, `lab`, `project`) encoded via `OneHotEncoder(handle_unknown='ignore')`.
- **Numeric (13)**:
  - `semester_number`: Academic progression level (1 to 4).
  - `attendance_percentage`: Cumulative attendance percentage up to cutoff.
  - `mst1_marks`: First Mid-Semester Test marks.
  - `mst2_marks`: Second Mid-Semester Test marks (or imputed if unheld).
  - `assignment_marks`: Continuous internal assignment evaluation marks.
  - `prior_sgpa`: Most recent prior finalized semester SGPA.
  - `prior_cgpa`: Cumulative Grade Point Average up to cutoff.
  - `viva_marks`: Practical laboratory viva voce marks (for practical courses).
  - `lab_journal_marks`: Lab record and continuous notebook evaluation score.
  - `synopsis_approved`: Binary indicator (1.0/0.0) of project synopsis clearance.
  - `design_approved`: Binary indicator (1.0/0.0) of architectural design sign-off.
  - `implementation_percentage`: Progress completion percentage on practical/project work.
  - `faculty_guide_interaction_score`: Mentorship engagement and review rating.

### 5.2 Semester-Level Features (8)
- All 8 features are continuous numeric indicators aggregated across enrolled courses:
  - `semester_number`: Semester sequence level (1 to 4).
  - `courses_included`: Count of active course registrations considered.
  - `mean_attendance_percentage`: Mean attendance percentage across all enrolled courses.
  - `mean_mst1_marks`: Mean Mid-Semester Test 1 score across enrolled courses.
  - `mean_mst2_marks`: Mean Mid-Semester Test 2 score across enrolled courses.
  - `mean_assignment_marks`: Mean continuous assignment marks across courses.
  - `mean_prior_sgpa`: Mean of prior finalized semester SGPAs.
  - `mean_prior_cgpa`: Historical cumulative GPA before the current semester.

### 5.3 Missing Data Strategy
- Numerical features with missing values are handled via `SimpleImputer(strategy='median')`.
- Missing values in raw database records are preserved as `None` in snapshots to ensure transparency. They are never artificially inflated.

---

## 6. Model Evaluation on Synthetic Holdout Split

### Subject-Level Model (Logistic Regression)
- **Accuracy**: 69.10%
- **Macro Precision**: 0.6812
- **Macro Recall**: 0.6698
- **Macro F1**: 0.6732

### Semester-Level Model (Random Forest)
- **Accuracy**: 70.42%
- **Macro Precision**: 0.7088
- **Macro Recall**: 0.6914
- **Macro F1**: 0.6973

> [!IMPORTANT]
> **Academic Integrity Notice**: These evaluation statistics were obtained strictly on synthetic holdout validation splits. They demonstrate methodological rigor, feature stability, and anti-leakage compliance. They must **never** be cited as empirical accuracy measurements on real UIT-RGPV student populations.
