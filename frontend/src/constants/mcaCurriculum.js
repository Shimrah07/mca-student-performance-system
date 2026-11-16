/**
 * frontend/src/constants/mcaCurriculum.js
 *
 * Formal curriculum specification for the Master of Computer Applications (MCA)
 * programme at University Institute of Technology — RGPV (Autonomous), Bhopal.
 *
 * Scope: 4 Semesters, 26 Confirmed Courses.
 *
 * Governance Rules:
 * - Subject codes and credit values are null unless officially confirmed by the examination scheme.
 * - Assessment marks and tier thresholds are not invented or hardcoded as university regulations.
 * - Confirmed elective tracks for Semester 3:
 *     Elective-I   : Python Programming
 *     Elective-II  : Machine Learning and Deep Learning
 *     Elective-III : Distributed Systems
 */

export const MCA_PROGRAM_METADATA = {
  program_name: "Master of Computer Applications",
  program_code: "MCA",
  degree: "Postgraduate (PG)",
  institution: "University Institute of Technology — RGPV (Autonomous), Bhopal",
  department: "Department of Computer Applications",
  total_semesters: 4,
  academic_session: "2026–27",
  source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum Roster",
  effective_date: "2026-27",
};

export const COURSE_TYPES = {
  THEORY: "theory",
  LAB: "lab",
  ELECTIVE: "elective",
  PROJECT: "project",
};

export const VERIFICATION_STATUS = {
  SYLLABUS_CONFIRMED: "syllabus_confirmed_code_pending",
  CONFIRMED: "confirmed",
  UNVERIFIED: "unverified",
};

export const MCA_SEMESTERS = [
  {
    semester_number: 1,
    name: "Semester 1",
    academic_focus: "Computing Foundations, Programming Systems & Core Engineering",
    subjects: [
      {
        id: "mca_sem1_os",
        name: "Operating System",
        code: "MCA108",
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 1 scheme.",
      },
      {
        id: "mca_sem1_c_prog",
        name: "Programming and Problem Solving in C",
        code: "MCA109",
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 1 scheme.",
      },
      {
        id: "mca_sem1_math",
        name: "Mathematical Foundation",
        code: "MCA110",
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 1 scheme.",
      },
      {
        id: "mca_sem1_fct",
        name: "Fundamentals of Computer Technologies",
        code: "MCA111",
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 1 scheme.",
      },
      {
        id: "mca_sem1_tc",
        name: "Technical Communication",
        code: "MCA112",
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 1 scheme.",
      },
      {
        id: "mca_sem1_c_lab",
        name: "Programming and Problem Solving in C Lab",
        code: "MCA113",
        course_type: COURSE_TYPES.LAB,
        elective_group: null,
        credits: 8,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 1 scheme (Practical Lab).",
      },
      {
        id: "mca_sem1_os_lab",
        name: "Operating System Lab",
        code: "MCA114",
        course_type: COURSE_TYPES.LAB,
        elective_group: null,
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 1 scheme (Practical Lab).",
      },
    ],
  },
  {
    semester_number: 2,
    name: "Semester 2",
    academic_focus: "Database Systems, Networking, OOP & Algorithm Design",
    subjects: [
      {
        id: "mca_sem2_dbms",
        name: "Database Management System",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
      {
        id: "mca_sem2_cn",
        name: "Computer Network",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
      {
        id: "mca_sem2_java",
        name: "Object Oriented Programming with Java",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
      {
        id: "mca_sem2_se_uml",
        name: "Software Engineering and UML",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
      {
        id: "mca_sem2_ada",
        name: "Algorithm Design",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
      {
        id: "mca_sem2_java_lab",
        name: "Java and OOPS Lab",
        code: null,
        course_type: COURSE_TYPES.LAB,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; practical lab course.",
      },
      {
        id: "mca_sem2_dbms_lab",
        name: "DBMS Lab",
        code: null,
        course_type: COURSE_TYPES.LAB,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; practical lab course.",
      },
    ],
  },
  {
    semester_number: 3,
    name: "Semester 3",
    academic_focus: "Data Mining, AI, Departmental Electives & Minor Project",
    subjects: [
      {
        id: "mca_sem3_dm",
        name: "Data Mining",
        code: "MCA301",
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 3 scheme.",
      },
      {
        id: "mca_sem3_ai",
        name: "Artificial Intelligence",
        code: "MCA302",
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 3 scheme.",
      },
      {
        id: "mca_sem3_elec1_python",
        name: "Elective-I: Python Programming",
        code: "MCA303",
        course_type: COURSE_TYPES.ELECTIVE,
        elective_group: "Elective-I",
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 3 scheme (Elective-I).",
      },
      {
        id: "mca_sem3_elec2_mldl",
        name: "Elective-II: Machine Learning and Deep Learning",
        code: "MCA304",
        course_type: COURSE_TYPES.ELECTIVE,
        elective_group: "Elective-II",
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 3 scheme (Elective-II).",
      },
      {
        id: "mca_sem3_elec3_ds",
        name: "Elective-III: Distributed Systems",
        code: "MCA305",
        course_type: COURSE_TYPES.ELECTIVE,
        elective_group: "Elective-III",
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 3 scheme (Elective-III).",
      },
      {
        id: "mca_sem3_minor_proj",
        name: "Minor Project",
        code: "MCA306",
        course_type: COURSE_TYPES.PROJECT,
        elective_group: null,
        credits: 8,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 3 scheme (Minor Project).",
      },
      {
        id: "mca_sem3_elec1_lab",
        name: "Elective-I Lab",
        code: "MCA307",
        course_type: COURSE_TYPES.LAB,
        elective_group: "Elective-I",
        credits: 4,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.CONFIRMED,
        verification_notes: "Course code and credits verified from official Semester 3 scheme (Elective-I Lab).",
      },
    ],
  },
  {
    semester_number: 4,
    name: "Semester 4",
    academic_focus: "Cloud, Blockchain, Advanced Computing & Enterprise Security",
    subjects: [
      {
        id: "mca_sem4_cct",
        name: "Cloud Computing Technologies",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
      {
        id: "mca_sem4_crypto",
        name: "Cryptocurrency and Blockchain Technologies",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
      {
        id: "mca_sem4_adv_python",
        name: "Advanced Python",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
      {
        id: "mca_sem4_is",
        name: "Information Security",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
      {
        id: "mca_sem4_bda",
        name: "Big Data Analytics",
        code: null,
        course_type: COURSE_TYPES.THEORY,
        elective_group: null,
        credits: null,
        source_scheme: "UIT-RGPV (Autonomous) MCA Curriculum",
        effective_date: "2026-27",
        verification_status: VERIFICATION_STATUS.SYLLABUS_CONFIRMED,
        verification_notes: "Subject details supplied by project owner; subject code pending verification.",
      },
    ],
  },
];

/**
 * Helper utilities for accessing MCA curriculum data
 */

export function getAllMcaCourses() {
  return MCA_SEMESTERS.flatMap((sem) =>
    sem.subjects.map((sub) => ({
      ...sub,
      semester_number: sem.semester_number,
      semester_name: sem.name,
    }))
  );
}

export function getMcaCoursesBySemester(semesterNumber) {
  const sem = MCA_SEMESTERS.find((s) => s.semester_number === Number(semesterNumber));
  return sem ? sem.subjects : [];
}

export function getMcaCourseById(courseId) {
  return getAllMcaCourses().find((c) => c.id === courseId) || null;
}

export function getMcaCoursesByType(courseType) {
  return getAllMcaCourses().filter((c) => c.course_type === courseType);
}

export function getElectivesBySemester(semesterNumber) {
  return getMcaCoursesBySemester(semesterNumber).filter(
    (c) => c.course_type === COURSE_TYPES.ELECTIVE
  );
}
