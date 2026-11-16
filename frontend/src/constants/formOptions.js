/**
 * Form field options, descriptions, and default sample templates
 * matching the approved UCI Student Performance dataset taxonomy.
 */

export const SUBJECT_OPTIONS = [
  { value: "Mathematics", label: "Mathematics (student-mat)" },
  { value: "Portuguese", label: "Portuguese Language (student-por)" },
];

export const SCENARIO_OPTIONS = [
  {
    value: "Scenario A",
    label: "Scenario A — Early-Warning Assessment",
    description: "Evaluates 30 demographic, behavioral, and study-habit factors. No formal exam marks required. Best for term start.",
  },
  {
    value: "Scenario B",
    label: "Scenario B — Mid-Term Diagnostic",
    description: "Evaluates 31 factors including First-Period Exam Grade (G1). Best for mid-semester intervention.",
  },
];

export const SCHOOL_OPTIONS = [
  { value: "GP", label: "GP — Gabriel Pereira" },
  { value: "MS", label: "MS — Mousinho da Silveira" },
];

export const SEX_OPTIONS = [
  { value: "F", label: "Female" },
  { value: "M", label: "Male" },
];

export const ADDRESS_OPTIONS = [
  { value: "U", label: "Urban" },
  { value: "R", label: "Rural" },
];

export const FAMSIZE_OPTIONS = [
  { value: "LE3", label: "3 members or fewer (LE3)" },
  { value: "GT3", label: "More than 3 members (GT3)" },
];

export const PSTATUS_OPTIONS = [
  { value: "T", label: "Living Together" },
  { value: "A", label: "Apart / Separated" },
];

export const JOB_OPTIONS = [
  { value: "teacher", label: "Education / Teacher" },
  { value: "health", label: "Healthcare / Medical" },
  { value: "services", label: "Civil or Administrative Services" },
  { value: "at_home", label: "Homemaker / At Home" },
  { value: "other", label: "Other" },
];

export const REASON_OPTIONS = [
  { value: "course", label: "Course Preference / Subject Interest" },
  { value: "reputation", label: "School Reputation" },
  { value: "home", label: "Close to Home" },
  { value: "other", label: "Other Reasons" },
];

export const GUARDIAN_OPTIONS = [
  { value: "mother", label: "Mother" },
  { value: "father", label: "Father" },
  { value: "other", label: "Other / Legal Guardian" },
];

export const EDU_LEVEL_OPTIONS = [
  { value: 0, label: "0 — None / No Formal Education" },
  { value: 1, label: "1 — Primary Education (4th Grade)" },
  { value: 2, label: "2 — 5th to 9th Grade" },
  { value: 3, label: "3 — Secondary Education" },
  { value: 4, label: "4 — Higher Education" },
];

export const TRAVELTIME_OPTIONS = [
  { value: 1, label: "1 — Under 15 minutes" },
  { value: 2, label: "2 — 15 to 30 minutes" },
  { value: 3, label: "3 — 30 to 60 minutes" },
  { value: 4, label: "4 — Over 60 minutes" },
];

export const STUDYTIME_OPTIONS = [
  { value: 1, label: "1 — Less than 2 hours per week" },
  { value: 2, label: "2 — 2 to 5 hours per week" },
  { value: 3, label: "3 — 5 to 10 hours per week" },
  { value: 4, label: "4 — More than 10 hours per week" },
];

export const FAILURES_OPTIONS = [
  { value: 0, label: "0 — No previous subject failures" },
  { value: 1, label: "1 — One previous failure" },
  { value: 2, label: "2 — Two previous failures" },
  { value: 3, label: "3 — Three previous failures" },
  { value: 4, label: "4 — Four or more previous failures" },
];

export const SCALE_1_TO_5 = [
  { value: 1, label: "1 — Very Low / Very Bad" },
  { value: 2, label: "2 — Low / Bad" },
  { value: 3, label: "3 — Moderate / Average" },
  { value: 4, label: "4 — High / Good" },
  { value: 5, label: "5 — Very High / Excellent" },
];

export const YES_NO_OPTIONS = [
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
];

/**
 * Pre-defined sample profiles for easy demonstration during evaluation.
 */
export const SAMPLE_PROFILES = {
  high_achiever: {
    label: "High Engagement Student (Aiming for Excellent)",
    subject: "Mathematics",
    scenario: "Scenario A",
    student_code: "STU-DEMO-001",
    features: {
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
      Mjob: "teacher",
      Fjob: "services",
      reason: "course",
      guardian: "mother",
      Medu: 4,
      Fedu: 4,
      traveltime: 1,
      studytime: 4,
      failures: 0,
      famrel: 5,
      freetime: 3,
      goout: 2,
      Dalc: 1,
      Walc: 1,
      health: 5,
      age: 16,
      absences: 2,
    },
  },
  needs_support: {
    label: "At-Risk Student (Early-Warning Support Needed)",
    subject: "Portuguese",
    scenario: "Scenario A",
    student_code: "STU-DEMO-002",
    features: {
      school: "MS",
      sex: "M",
      address: "R",
      famsize: "GT3",
      Pstatus: "A",
      schoolsup: "no",
      famsup: "no",
      paid: "no",
      activities: "no",
      nursery: "no",
      higher: "no",
      internet: "no",
      romantic: "yes",
      Mjob: "at_home",
      Fjob: "other",
      reason: "home",
      guardian: "father",
      Medu: 1,
      Fedu: 1,
      traveltime: 3,
      studytime: 1,
      failures: 2,
      famrel: 2,
      freetime: 4,
      goout: 4,
      Dalc: 3,
      Walc: 4,
      health: 2,
      age: 18,
      absences: 14,
    },
  },
  midterm_diagnostic: {
    label: "Mid-Term Diagnostic with G1 (Scenario B)",
    subject: "Mathematics",
    scenario: "Scenario B",
    student_code: "STU-DEMO-003",
    features: {
      school: "GP",
      sex: "F",
      address: "U",
      famsize: "LE3",
      Pstatus: "T",
      schoolsup: "yes",
      famsup: "yes",
      paid: "yes",
      activities: "yes",
      nursery: "yes",
      higher: "yes",
      internet: "yes",
      romantic: "no",
      Mjob: "services",
      Fjob: "services",
      reason: "reputation",
      guardian: "mother",
      Medu: 3,
      Fedu: 3,
      traveltime: 1,
      studytime: 2,
      failures: 0,
      famrel: 4,
      freetime: 3,
      goout: 3,
      Dalc: 1,
      Walc: 2,
      health: 4,
      age: 16,
      absences: 4,
      G1: 13,
    },
  },
};
