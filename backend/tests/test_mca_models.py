"""
backend/tests/test_mca_models.py

Automated test suite for Phase 2C: MCA ORM Model and Database Constraint Tests.
Verifies all 13 MCA SQLAlchemy models, 19 foreign keys, unique constraints,
check constraints, indexes, and deletion protection against the Phase 2B Final
Implementation Contract.

Strict isolation:
- Operates strictly on an in-memory SQLite database (`sqlite:///:memory:`).
- Enables SQLite foreign-key enforcement explicitly (`PRAGMA foreign_keys=ON`).
- Never connects to MySQL and never modifies shared database configurations.
- Pure ORM test: does not depend on pandas or machine learning libraries.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, Session

from app.models import (
    Base,
    MCAProgram,
    MCACurriculumScheme,
    MCACourse,
    MCAAcademicSession,
    MCASessionCourse,
    MCAStudent,
    MCACourseRegistration,
    MCAAssessmentEvent,
    MCAAttendanceSnapshot,
    MCAFormativeSnapshot,
    MCAProjectMilestoneSnapshot,
    MCASemesterResult,
    MCAPredictionRecord,
)


# ===========================================================================
# Isolated SQLite Test Fixtures
# ===========================================================================

@pytest.fixture
def mca_engine():
    """
    Provide an isolated in-memory SQLite database engine with foreign-key
    enforcement enabled via PRAGMA.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all registered tables (both Phase 1 and Phase 2B MCA tables)
    Base.metadata.create_all(bind=engine)
    yield engine
    # Disable foreign keys during teardown so drop_all does not fail on self-referencing rows
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        Base.metadata.drop_all(bind=conn)
    engine.dispose()


@pytest.fixture
def mca_session(mca_engine) -> Session:
    """
    Provide a clean transactional session bound to the isolated in-memory engine.
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mca_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def base_hierarchy(mca_session):
    """
    Seed minimal parent entities required for downstream foreign keys:
    Program -> Scheme -> Course -> Session -> SessionCourse -> Student.
    """
    program = MCAProgram(
        program_name="Master of Computer Applications",
        program_code="MCA",
        duration_semesters=4,
    )
    mca_session.add(program)
    mca_session.flush()

    scheme = MCACurriculumScheme(
        program_id=program.id,
        scheme_name="UIT-RGPV Autonomous MCA Curriculum",
        scheme_code="MCA-AUTONOMOUS-2026",
        effective_from="2026-27",
        is_active=True,
    )
    mca_session.add(scheme)
    mca_session.flush()

    course = MCACourse(
        program_id=program.id,
        scheme_id=scheme.id,
        course_code="MCA108",
        course_name="Operating System",
        semester_number=1,
        course_type="theory",
        elective_group=None,
        credits=4,
    )
    mca_session.add(course)
    mca_session.flush()

    academic_session = MCAAcademicSession(
        scheme_id=scheme.id,
        session_name="MCA 2025-27 Batch",
        batch_year="2025-2027",
        start_date=date(2025, 8, 1),
        end_date=date(2027, 6, 30),
        is_active=True,
    )
    mca_session.add(academic_session)
    mca_session.flush()

    session_course = MCASessionCourse(
        session_id=academic_session.id,
        course_id=course.id,
    )
    mca_session.add(session_course)
    mca_session.flush()

    student = MCAStudent(
        student_code="MCA-2026-001",
        session_id=academic_session.id,
        is_active=True,
    )
    mca_session.add(student)
    mca_session.flush()

    mca_session.commit()

    return {
        "program": program,
        "scheme": scheme,
        "course": course,
        "academic_session": academic_session,
        "session_course": session_course,
        "student": student,
    }


# ===========================================================================
# A. Metadata and Registration Tests
# ===========================================================================

class TestMCAMetadata:
    def test_all_13_mca_tables_registered(self):
        """Verify all 13 MCA table names are registered in Base.metadata.tables."""
        expected_mca_tables = {
            "mca_programs",
            "mca_curriculum_schemes",
            "mca_courses",
            "mca_academic_sessions",
            "mca_session_courses",
            "mca_students",
            "mca_course_registrations",
            "mca_assessment_events",
            "mca_attendance_snapshots",
            "mca_formative_snapshots",
            "mca_project_milestone_snapshots",
            "mca_semester_results",
            "mca_prediction_records",
        }
        registered = set(Base.metadata.tables.keys())
        assert expected_mca_tables.issubset(registered), (
            f"Missing MCA tables: {expected_mca_tables - registered}"
        )

    def test_phase1_uci_tables_preserved(self):
        """Verify original Phase 1 UCI tables remain registered and unmodified."""
        registered = set(Base.metadata.tables.keys())
        assert "students" in registered, "Original 'students' table missing from metadata"
        assert "prediction_records" in registered, "Original 'prediction_records' table missing from metadata"

    def test_total_table_count(self):
        """Verify exactly 15 tables are registered (13 MCA + 2 Phase 1 UCI)."""
        registered = set(Base.metadata.tables.keys())
        assert len(registered) == 15, f"Expected 15 tables in Base.metadata, found {len(registered)}: {registered}"

    def test_exact_19_foreign_keys_registered(self):
        """Verify that exactly 19 foreign keys exist across the 13 MCA tables."""
        mca_table_names = [
            "mca_programs", "mca_curriculum_schemes", "mca_courses",
            "mca_academic_sessions", "mca_session_courses", "mca_students",
            "mca_course_registrations", "mca_assessment_events",
            "mca_attendance_snapshots", "mca_formative_snapshots",
            "mca_project_milestone_snapshots", "mca_semester_results",
            "mca_prediction_records",
        ]
        fk_count = 0
        for tname in mca_table_names:
            table = Base.metadata.tables[tname]
            fk_count += len(table.foreign_keys)

        assert fk_count == 19, f"Expected exactly 19 MCA foreign keys, found {fk_count}"

    def test_column_definitions_and_nullability(self):
        """Verify key columns, types, nullability, and defaults against the contract."""
        # 1. mca_programs
        prog = Base.metadata.tables["mca_programs"]
        assert prog.columns["program_code"].nullable is False
        assert prog.columns["duration_semesters"].default.arg == 4

        # 2. mca_curriculum_schemes
        sch = Base.metadata.tables["mca_curriculum_schemes"]
        assert sch.columns["scheme_code"].nullable is False
        assert sch.columns["effective_until"].nullable is True

        # 3. mca_courses
        crs = Base.metadata.tables["mca_courses"]
        assert crs.columns["scheme_id"].nullable is True  # provisional courses support
        assert crs.columns["course_code"].nullable is True

        # 4. mca_academic_sessions
        sess = Base.metadata.tables["mca_academic_sessions"]
        assert sess.columns["session_name"].nullable is False
        assert sess.columns["is_active"].nullable is False

        # 5. mca_session_courses
        sc = Base.metadata.tables["mca_session_courses"]
        assert len(sc.columns) == 3

        # 6. mca_students
        stu = Base.metadata.tables["mca_students"]
        assert stu.columns["student_code"].nullable is False
        assert stu.columns["is_active"].nullable is False
        assert stu.columns["deactivated_at"].nullable is True
        assert stu.columns["deactivation_reason"].nullable is True

        # 7. mca_course_registrations
        reg = Base.metadata.tables["mca_course_registrations"]
        assert reg.columns["attempt_type"].nullable is False
        assert reg.columns["attempt_type"].default.arg == "regular"
        assert reg.columns["is_active"].nullable is False

        # 8. mca_assessment_events (has created_at, exactly 8 columns)
        ev = Base.metadata.tables["mca_assessment_events"]
        assert len(ev.columns) == 8
        assert ev.columns["original_event_id"].nullable is True
        assert "created_at" in ev.columns

        # 9, 10, 11. Snapshots: verify revision_number and recorded_at
        for snap_tname in ["mca_attendance_snapshots", "mca_formative_snapshots", "mca_project_milestone_snapshots"]:
            snap = Base.metadata.tables[snap_tname]
            assert "revision_number" in snap.columns, f"{snap_tname} missing revision_number"
            assert "recorded_at" in snap.columns, f"{snap_tname} missing recorded_at"
            assert snap.columns["revision_number"].nullable is False
            assert snap.columns["recorded_at"].nullable is False

        # 12. mca_semester_results: verify declared_at (nullable) and recorded_at (not null), cgpa
        res = Base.metadata.tables["mca_semester_results"]
        assert res.columns["declared_at"].nullable is True
        assert res.columns["recorded_at"].nullable is False
        assert res.columns["cgpa"].nullable is True

        # 13. mca_prediction_records: cutoff_timestamp separate from created_at
        pred = Base.metadata.tables["mca_prediction_records"]
        assert "cutoff_timestamp" in pred.columns
        assert "created_at" in pred.columns
        assert pred.columns["cutoff_timestamp"].nullable is False
        assert pred.columns["student_id"].nullable is True
        assert pred.columns["registration_id"].nullable is True
        assert pred.columns["course_id"].nullable is True


# ===========================================================================
# B. Foreign-Key Verification Tests (All 19 FKs and ondelete Actions)
# ===========================================================================

class TestMCAForeignKeys:
    def test_foreign_key_ondelete_actions(self):
        """Inspect all 19 foreign-key specifications and verify exact ondelete actions."""
        expected_fks = {
            # (table, column): (target_table, target_column, ondelete)
            ("mca_curriculum_schemes", "program_id"): ("mca_programs", "id", "RESTRICT"),
            ("mca_courses", "program_id"): ("mca_programs", "id", "RESTRICT"),
            ("mca_courses", "scheme_id"): ("mca_curriculum_schemes", "id", "RESTRICT"),
            ("mca_academic_sessions", "scheme_id"): ("mca_curriculum_schemes", "id", "RESTRICT"),
            ("mca_session_courses", "session_id"): ("mca_academic_sessions", "id", "RESTRICT"),
            ("mca_session_courses", "course_id"): ("mca_courses", "id", "RESTRICT"),
            ("mca_students", "session_id"): ("mca_academic_sessions", "id", "RESTRICT"),
            ("mca_course_registrations", "student_id"): ("mca_students", "id", "RESTRICT"),
            ("mca_course_registrations", "session_course_id"): ("mca_session_courses", "id", "RESTRICT"),
            ("mca_assessment_events", "session_course_id"): ("mca_session_courses", "id", "RESTRICT"),
            ("mca_assessment_events", "original_event_id"): ("mca_assessment_events", "id", "RESTRICT"),
            ("mca_attendance_snapshots", "registration_id"): ("mca_course_registrations", "id", "RESTRICT"),
            ("mca_formative_snapshots", "registration_id"): ("mca_course_registrations", "id", "RESTRICT"),
            ("mca_project_milestone_snapshots", "registration_id"): ("mca_course_registrations", "id", "RESTRICT"),
            ("mca_semester_results", "student_id"): ("mca_students", "id", "RESTRICT"),
            ("mca_semester_results", "session_id"): ("mca_academic_sessions", "id", "RESTRICT"),
            ("mca_prediction_records", "student_id"): ("mca_students", "id", "SET NULL"),
            ("mca_prediction_records", "registration_id"): ("mca_course_registrations", "id", "SET NULL"),
            ("mca_prediction_records", "course_id"): ("mca_courses", "id", "RESTRICT"),
        }

        # Assert total expected count is exactly 19
        assert len(expected_fks) == 19, f"Expected 19 foreign keys in contract, got {len(expected_fks)}"

        # Assert exact distribution: 17 RESTRICT, 2 SET NULL, 0 CASCADE
        restrict_count = sum(1 for v in expected_fks.values() if v[2] == "RESTRICT")
        set_null_count = sum(1 for v in expected_fks.values() if v[2] == "SET NULL")
        cascade_count = sum(1 for v in expected_fks.values() if v[2] == "CASCADE")
        assert restrict_count == 17, f"Expected 17 RESTRICT FKs, found {restrict_count}"
        assert set_null_count == 2, f"Expected 2 SET NULL FKs, found {set_null_count}"
        assert cascade_count == 0, f"Expected 0 CASCADE FKs, found {cascade_count}"

        # Assert every FK matches metadata
        total_mca_fks_found = 0
        for (table_name, col_name), (tgt_table, tgt_col, ondelete) in expected_fks.items():
            table = Base.metadata.tables[table_name]
            matching_fks = [
                fk for fk in table.foreign_keys
                if fk.parent.name == col_name and fk.column.table.name == tgt_table and fk.column.name == tgt_col
            ]
            assert len(matching_fks) == 1, f"Missing FK on {table_name}.{col_name} -> {tgt_table}.{tgt_col}"
            fk = matching_fks[0]
            assert fk.ondelete.upper() == ondelete, (
                f"Mismatch on {table_name}.{col_name}: expected ondelete={ondelete}, found {fk.ondelete}"
            )
            total_mca_fks_found += 1

        assert total_mca_fks_found == 19

        # Ensure no accidental CASCADE foreign keys exist on ANY MCA table
        mca_table_names = [k[0] for k in expected_fks.keys()]
        for tname in set(mca_table_names):
            table = Base.metadata.tables[tname]
            for fk in table.foreign_keys:
                action = (fk.ondelete or "").upper()
                assert action != "CASCADE", f"Unapproved CASCADE action found on {tname}.{fk.parent.name}"

    def test_foreign_key_violation_on_insert(self, mca_session):
        """Verify inserting an entity with a non-existent parent FK fails under PRAGMA foreign_keys=ON."""
        # Non-existent program_id
        invalid_scheme = MCACurriculumScheme(
            program_id=99999,
            scheme_name="Ghost Scheme",
            scheme_code="GHOST-01",
            effective_from="2026-27",
        )
        mca_session.add(invalid_scheme)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

        # Non-existent session_id on student
        invalid_student = MCAStudent(
            student_code="MCA-GHOST-001",
            session_id=99999,
        )
        mca_session.add(invalid_student)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()


# ===========================================================================
# C. Unique Constraints Tests
# ===========================================================================

class TestMCAUniqueConstraints:
    def test_unique_program_code(self, mca_session, base_hierarchy):
        """Verify duplicate program_code raises IntegrityError."""
        dup = MCAProgram(
            program_name="Duplicate MCA Program",
            program_code="MCA",  # already exists in base_hierarchy
        )
        mca_session.add(dup)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

    def test_unique_scheme_code(self, mca_session, base_hierarchy):
        """Verify duplicate scheme_code raises IntegrityError."""
        dup = MCACurriculumScheme(
            program_id=base_hierarchy["program"].id,
            scheme_name="Duplicate Scheme",
            scheme_code="MCA-AUTONOMOUS-2026",
            effective_from="2026-27",
        )
        mca_session.add(dup)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

    def test_unique_course_program_code(self, mca_session, base_hierarchy):
        """Verify duplicate (program_id, course_code) raises IntegrityError."""
        dup = MCACourse(
            program_id=base_hierarchy["program"].id,
            course_code="MCA108",  # already in program
            course_name="OS Duplicate",
            semester_number=1,
            course_type="theory",
        )
        mca_session.add(dup)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

    def test_nullable_course_code_uniqueness_behavior(self, mca_session, base_hierarchy):
        """Verify multiple courses with NULL course_code can coexist under same program."""
        c1 = MCACourse(
            program_id=base_hierarchy["program"].id,
            course_code=None,
            course_name="Provisional Course 1",
            semester_number=2,
            course_type="theory",
        )
        c2 = MCACourse(
            program_id=base_hierarchy["program"].id,
            course_code=None,
            course_name="Provisional Course 2",
            semester_number=2,
            course_type="lab",
        )
        mca_session.add_all([c1, c2])
        mca_session.flush()
        assert c1.id is not None
        assert c2.id is not None
        mca_session.rollback()

    def test_unique_session_scheme_name(self, mca_session, base_hierarchy):
        """Verify duplicate (scheme_id, session_name) raises IntegrityError."""
        dup = MCAAcademicSession(
            scheme_id=base_hierarchy["scheme"].id,
            session_name="MCA 2025-27 Batch",
            batch_year="2025-2027",
            start_date=date(2025, 8, 1),
            end_date=date(2027, 6, 30),
        )
        mca_session.add(dup)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

    def test_unique_session_course(self, mca_session, base_hierarchy):
        """Verify duplicate (session_id, course_id) raises IntegrityError."""
        dup = MCASessionCourse(
            session_id=base_hierarchy["academic_session"].id,
            course_id=base_hierarchy["course"].id,
        )
        mca_session.add(dup)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

    def test_unique_student_code(self, mca_session, base_hierarchy):
        """Verify duplicate student_code raises IntegrityError."""
        dup = MCAStudent(
            student_code="MCA-2026-001",
            session_id=base_hierarchy["academic_session"].id,
        )
        mca_session.add(dup)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

    def test_unique_snapshot_revisions(self, mca_session, base_hierarchy):
        """Verify duplicate (registration_id, revision_number) in all 3 snapshot tables."""
        reg = MCACourseRegistration(
            student_id=base_hierarchy["student"].id,
            session_course_id=base_hierarchy["session_course"].id,
            semester_number=1,
            attempt_type="regular",
        )
        mca_session.add(reg)
        mca_session.flush()

        # 1. Attendance Snapshot duplicate
        att1 = MCAAttendanceSnapshot(registration_id=reg.id, revision_number=1, attendance_percentage=85.0)
        att2 = MCAAttendanceSnapshot(registration_id=reg.id, revision_number=1, attendance_percentage=90.0)
        mca_session.add(att1)
        mca_session.flush()
        mca_session.add(att2)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

        # Re-query reg after rollback
        reg = mca_session.get(MCACourseRegistration, reg.id) or MCACourseRegistration(
            student_id=base_hierarchy["student"].id,
            session_course_id=base_hierarchy["session_course"].id,
            semester_number=1,
            attempt_type="regular",
        )
        if reg.id is None:
            mca_session.add(reg)
            mca_session.flush()

        # 2. Formative Snapshot duplicate
        form1 = MCAFormativeSnapshot(registration_id=reg.id, revision_number=1, mst1_marks=18.0)
        form2 = MCAFormativeSnapshot(registration_id=reg.id, revision_number=1, mst1_marks=19.0)
        mca_session.add(form1)
        mca_session.flush()
        mca_session.add(form2)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

        # 3. Project Milestone Snapshot duplicate
        reg = MCACourseRegistration(
            student_id=base_hierarchy["student"].id,
            session_course_id=base_hierarchy["session_course"].id,
            semester_number=1,
            attempt_type="regular",
        )
        mca_session.add(reg)
        mca_session.flush()

        mile1 = MCAProjectMilestoneSnapshot(registration_id=reg.id, revision_number=1, synopsis_approved=True)
        mile2 = MCAProjectMilestoneSnapshot(registration_id=reg.id, revision_number=1, synopsis_approved=False)
        mca_session.add(mile1)
        mca_session.flush()
        mca_session.add(mile2)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()


# ===========================================================================
# D. Check Constraints Tests
# ===========================================================================

class TestMCACheckConstraints:
    def test_course_semester_number_check(self, mca_session, base_hierarchy):
        """Verify semester_number IN (1, 2, 3, 4) on mca_courses: valid (1..4) and invalid (<1, >4)."""
        program_id = base_hierarchy["program"].id

        # Valid values: 1, 2, 3, 4
        for sem in [1, 2, 3, 4]:
            c = MCACourse(
                program_id=program_id,
                course_name=f"Valid Sem Course {sem}",
                semester_number=sem,
                course_type="theory",
            )
            mca_session.add(c)
            mca_session.flush()
        mca_session.rollback()

        # Invalid values: 0, 5, -1
        for invalid_sem in [0, 5, -1]:
            bad_course = MCACourse(
                program_id=program_id,
                course_name=f"Invalid Sem Course {invalid_sem}",
                semester_number=invalid_sem,
                course_type="theory",
            )
            mca_session.add(bad_course)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

    def test_registration_semester_number_check(self, mca_session, base_hierarchy):
        """Verify semester_number IN (1, 2, 3, 4) on mca_course_registrations: valid (1..4) and invalid (<1, >4)."""
        student_id = base_hierarchy["student"].id
        sc_id = base_hierarchy["session_course"].id

        # Valid values: 1, 2, 3, 4
        for sem in [1, 2, 3, 4]:
            reg = MCACourseRegistration(
                student_id=student_id,
                session_course_id=sc_id,
                semester_number=sem,
                attempt_type="regular",
            )
            mca_session.add(reg)
            mca_session.flush()
        mca_session.rollback()

        # Invalid values: 0, 5, -1
        for invalid_sem in [0, 5, -1]:
            bad_reg = MCACourseRegistration(
                student_id=student_id,
                session_course_id=sc_id,
                semester_number=invalid_sem,
                attempt_type="regular",
            )
            mca_session.add(bad_reg)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

    def test_semester_result_semester_number_check(self, mca_session, base_hierarchy):
        """Verify semester_number IN (1, 2, 3, 4) on mca_semester_results: valid (1..4) and invalid (<1, >4)."""
        student_id = base_hierarchy["student"].id
        session_id = base_hierarchy["academic_session"].id

        # Valid values: 1, 2, 3, 4
        for sem in [1, 2, 3, 4]:
            res = MCASemesterResult(
                student_id=student_id,
                session_id=session_id,
                semester_number=sem,
                sgpa=Decimal("8.00"),
            )
            mca_session.add(res)
            mca_session.flush()
        mca_session.rollback()

        # Invalid values: 0, 5, -1
        for invalid_sem in [0, 5, -1]:
            bad_res = MCASemesterResult(
                student_id=student_id,
                session_id=session_id,
                semester_number=invalid_sem,
                sgpa=Decimal("8.00"),
            )
            mca_session.add(bad_res)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

    def test_course_type_check(self, mca_session, base_hierarchy):
        """Verify course_type IN ('theory', 'lab', 'elective', 'project') on mca_courses."""
        program_id = base_hierarchy["program"].id

        # Valid permitted types: 'theory', 'lab', 'elective', 'project'
        for valid_type in ["theory", "lab", "elective", "project"]:
            c = MCACourse(
                program_id=program_id,
                course_name=f"Course of type {valid_type}",
                semester_number=1,
                course_type=valid_type,
            )
            mca_session.add(c)
            mca_session.flush()
        mca_session.rollback()

        # Invalid unapproved types: 'CORE', 'seminar', 'ELECTIVE', 'audit', ''
        for invalid_type in ["CORE", "seminar", "ELECTIVE", "audit", ""]:
            bad_course = MCACourse(
                program_id=program_id,
                course_name=f"Invalid Type {invalid_type}",
                semester_number=1,
                course_type=invalid_type,
            )
            mca_session.add(bad_course)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

    def test_registration_attempt_type_check(self, mca_session, base_hierarchy):
        """Verify attempt_type IN ('regular', 'backlog', 'supplementary', 'improvement') on mca_course_registrations."""
        student_id = base_hierarchy["student"].id
        sc_id = base_hierarchy["session_course"].id

        # Valid permitted attempt types: 'regular', 'backlog', 'supplementary', 'improvement'
        for valid_attempt in ["regular", "backlog", "supplementary", "improvement"]:
            reg = MCACourseRegistration(
                student_id=student_id,
                session_course_id=sc_id,
                semester_number=1,
                attempt_type=valid_attempt,
            )
            mca_session.add(reg)
            mca_session.flush()
        mca_session.rollback()

        # Invalid unapproved attempt types: 'FIRST_ATTEMPT', 'REPEAT', 'MAKEUP', 'audit', ''
        for invalid_attempt in ["FIRST_ATTEMPT", "REPEAT", "MAKEUP", "audit", ""]:
            bad_reg = MCACourseRegistration(
                student_id=student_id,
                session_course_id=sc_id,
                semester_number=1,
                attempt_type=invalid_attempt,
            )
            mca_session.add(bad_reg)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

    def test_assessment_event_max_marks_check(self, mca_session, base_hierarchy):
        """Verify max_marks > 0 check constraint on mca_assessment_events."""
        sc_id = base_hierarchy["session_course"].id

        # Valid positive values: 20.00, 0.01, 100.00
        for valid_marks in [Decimal("20.00"), Decimal("0.01"), Decimal("100.00")]:
            ev = MCAAssessmentEvent(
                session_course_id=sc_id,
                event_name=f"Valid Mark Test {valid_marks}",
                event_type="MST",
                max_marks=valid_marks,
            )
            mca_session.add(ev)
            mca_session.flush()
        mca_session.rollback()

        # Invalid values: 0.00, -5.00
        for invalid_marks in [Decimal("0.00"), Decimal("-5.00")]:
            bad_ev = MCAAssessmentEvent(
                session_course_id=sc_id,
                event_name=f"Invalid Mark Test {invalid_marks}",
                event_type="MST",
                max_marks=invalid_marks,
            )
            mca_session.add(bad_ev)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

    def test_assessment_event_original_event_id_not_self_check(self, mca_session, base_hierarchy):
        """Verify original_event_id IS NULL OR original_event_id != id on mca_assessment_events."""
        sc_id = base_hierarchy["session_course"].id

        # Valid: original_event_id is None
        orig_ev = MCAAssessmentEvent(
            session_course_id=sc_id,
            event_name="Original Midterm",
            event_type="MST",
            max_marks=Decimal("20.00"),
            original_event_id=None,
        )
        mca_session.add(orig_ev)
        mca_session.flush()

        # Valid: original_event_id points to another event
        makeup_ev = MCAAssessmentEvent(
            session_course_id=sc_id,
            event_name="Makeup Midterm",
            event_type="MAKEUP",
            max_marks=Decimal("20.00"),
            original_event_id=orig_ev.id,
        )
        mca_session.add(makeup_ev)
        mca_session.flush()

        # Invalid: updating original_event_id to point to self (event.id)
        with pytest.raises((IntegrityError, ValueError)):
            orig_ev.original_event_id = orig_ev.id
            mca_session.flush()
        mca_session.rollback()

        # Invalid: direct insert where id == original_event_id
        with pytest.raises((IntegrityError, ValueError)):
            self_loop_ev = MCAAssessmentEvent(
                id=77777,
                session_course_id=sc_id,
                event_name="Direct Self Loop",
                event_type="MST",
                max_marks=Decimal("20.00"),
                original_event_id=77777,
            )
            mca_session.add(self_loop_ev)
            mca_session.flush()
        mca_session.rollback()

    def test_snapshot_revision_positive_check(self, mca_session, base_hierarchy):
        """Verify revision_number >= 1 on all three snapshot tables."""
        reg = MCACourseRegistration(
            student_id=base_hierarchy["student"].id,
            session_course_id=base_hierarchy["session_course"].id,
            semester_number=1,
        )
        mca_session.add(reg)
        mca_session.commit()

        # 1. mca_attendance_snapshots
        # Valid: 1, 2
        for rev in [1, 2]:
            snap = MCAAttendanceSnapshot(registration_id=reg.id, revision_number=rev, attendance_percentage=Decimal("85.00"))
            mca_session.add(snap)
            mca_session.flush()
        mca_session.rollback()

        # Invalid: 0, -1
        for bad_rev in [0, -1]:
            bad_snap = MCAAttendanceSnapshot(registration_id=reg.id, revision_number=bad_rev, attendance_percentage=Decimal("85.00"))
            mca_session.add(bad_snap)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

        # 2. mca_formative_snapshots
        # Valid: 1, 2
        for rev in [1, 2]:
            snap = MCAFormativeSnapshot(registration_id=reg.id, revision_number=rev, mst1_marks=Decimal("18.00"))
            mca_session.add(snap)
            mca_session.flush()
        mca_session.rollback()

        # Invalid: 0, -1
        for bad_rev in [0, -1]:
            bad_snap = MCAFormativeSnapshot(registration_id=reg.id, revision_number=bad_rev, mst1_marks=Decimal("18.00"))
            mca_session.add(bad_snap)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

        # 3. mca_project_milestone_snapshots
        # Valid: 1, 2
        for rev in [1, 2]:
            snap = MCAProjectMilestoneSnapshot(registration_id=reg.id, revision_number=rev, synopsis_approved=True)
            mca_session.add(snap)
            mca_session.flush()
        mca_session.rollback()

        # Invalid: 0, -1
        for bad_rev in [0, -1]:
            bad_snap = MCAProjectMilestoneSnapshot(registration_id=reg.id, revision_number=bad_rev, synopsis_approved=True)
            mca_session.add(bad_snap)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

    def test_attendance_percentage_check(self, mca_session, base_hierarchy):
        """Verify attendance_percentage IS NULL OR BETWEEN 0.00 AND 100.00 on mca_attendance_snapshots."""
        reg = MCACourseRegistration(
            student_id=base_hierarchy["student"].id,
            session_course_id=base_hierarchy["session_course"].id,
            semester_number=1,
        )
        mca_session.add(reg)
        mca_session.commit()

        # Valid values: None (NULL), 0.00, 75.50, 100.00
        valid_pcts = [None, Decimal("0.00"), Decimal("75.50"), Decimal("100.00")]
        for i, val in enumerate(valid_pcts, start=1):
            snap = MCAAttendanceSnapshot(
                registration_id=reg.id,
                revision_number=i,
                attendance_percentage=val,
            )
            mca_session.add(snap)
            mca_session.flush()
        mca_session.rollback()

        # Invalid values: -0.01, 100.01, 105.00
        for invalid_pct in [Decimal("-0.01"), Decimal("100.01"), Decimal("105.00")]:
            bad_snap = MCAAttendanceSnapshot(
                registration_id=reg.id,
                revision_number=1,
                attendance_percentage=invalid_pct,
            )
            mca_session.add(bad_snap)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

    def test_semester_result_sgpa_range_check(self, mca_session, base_hierarchy):
        """Verify sgpa BETWEEN 0.00 AND 10.00 on mca_semester_results."""
        student_id = base_hierarchy["student"].id
        session_id = base_hierarchy["academic_session"].id

        # Valid values: 0.00, 7.85, 10.00
        for val in [Decimal("0.00"), Decimal("7.85"), Decimal("10.00")]:
            res = MCASemesterResult(
                student_id=student_id,
                session_id=session_id,
                semester_number=1,
                sgpa=val,
            )
            mca_session.add(res)
            mca_session.flush()
        mca_session.rollback()

        # Invalid values: -0.01, 10.01, 11.50
        for invalid_val in [Decimal("-0.01"), Decimal("10.01"), Decimal("11.50")]:
            bad_res = MCASemesterResult(
                student_id=student_id,
                session_id=session_id,
                semester_number=1,
                sgpa=invalid_val,
            )
            mca_session.add(bad_res)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()

    def test_semester_result_cgpa_range_check(self, mca_session, base_hierarchy):
        """Verify cgpa IS NULL OR (cgpa BETWEEN 0.00 AND 10.00) on mca_semester_results."""
        student_id = base_hierarchy["student"].id
        session_id = base_hierarchy["academic_session"].id

        # Valid values: None (NULL), 0.00, 8.50, 10.00
        for val in [None, Decimal("0.00"), Decimal("8.50"), Decimal("10.00")]:
            res = MCASemesterResult(
                student_id=student_id,
                session_id=session_id,
                semester_number=1,
                sgpa=Decimal("8.00"),
                cgpa=val,
            )
            mca_session.add(res)
            mca_session.flush()
        mca_session.rollback()

        # Invalid values: -0.01, 10.01, 11.50
        for invalid_val in [Decimal("-0.01"), Decimal("10.01"), Decimal("11.50")]:
            bad_res = MCASemesterResult(
                student_id=student_id,
                session_id=session_id,
                semester_number=1,
                sgpa=Decimal("8.00"),
                cgpa=invalid_val,
            )
            mca_session.add(bad_res)
            with pytest.raises(IntegrityError):
                mca_session.flush()
            mca_session.rollback()


# ===========================================================================
# E. Relationships and Deletion Protection Tests
# ===========================================================================

class TestMCARelationshipsAndDeletions:
    def test_assessment_event_original_makeup_relationship(self, mca_session, base_hierarchy):
        """Verify bidirectional original_event / makeup_events relationship traversal."""
        original = MCAAssessmentEvent(
            session_course_id=base_hierarchy["session_course"].id,
            event_name="MST 1 Regular",
            event_type="MST",
            max_marks=20.00,
            original_event_id=None,
        )
        mca_session.add(original)
        mca_session.flush()

        makeup = MCAAssessmentEvent(
            session_course_id=base_hierarchy["session_course"].id,
            event_name="MST 1 Makeup",
            event_type="MAKEUP",
            max_marks=20.00,
            original_event_id=original.id,
        )
        mca_session.add(makeup)
        mca_session.flush()

        # Test relationship traversal in both directions
        assert makeup.original_event == original
        assert original.makeup_events == [makeup]

    def test_restrict_prevents_parent_deletion_with_registrations(self, mca_session, base_hierarchy):
        """Verify RESTRICT on mca_course_registrations.student_id prevents deleting student."""
        reg = MCACourseRegistration(
            student_id=base_hierarchy["student"].id,
            session_course_id=base_hierarchy["session_course"].id,
            semester_number=1,
            attempt_type="regular",
        )
        mca_session.add(reg)
        mca_session.commit()

        # Attempting to delete student with registrations must raise IntegrityError
        mca_session.delete(base_hierarchy["student"])
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

    def test_restrict_prevents_registration_deletion_with_snapshots(self, mca_session, base_hierarchy):
        """Verify RESTRICT on mca_attendance_snapshots prevents deleting course registration."""
        reg = MCACourseRegistration(
            student_id=base_hierarchy["student"].id,
            session_course_id=base_hierarchy["session_course"].id,
            semester_number=1,
        )
        mca_session.add(reg)
        mca_session.flush()

        snap = MCAAttendanceSnapshot(
            registration_id=reg.id,
            revision_number=1,
            attendance_percentage=92.00,
        )
        mca_session.add(snap)
        mca_session.commit()

        mca_session.delete(reg)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

    def test_restrict_prevents_original_event_deletion_with_makeups(self, mca_session, base_hierarchy):
        """Verify RESTRICT on original_event_id prevents deleting an original event with makeups."""
        original = MCAAssessmentEvent(
            session_course_id=base_hierarchy["session_course"].id,
            event_name="MST 2 Regular",
            event_type="MST",
            max_marks=20.00,
        )
        mca_session.add(original)
        mca_session.flush()

        makeup = MCAAssessmentEvent(
            session_course_id=base_hierarchy["session_course"].id,
            event_name="MST 2 Makeup",
            event_type="MAKEUP",
            max_marks=20.00,
            original_event_id=original.id,
        )
        mca_session.add(makeup)
        mca_session.commit()

        mca_session.delete(original)
        with pytest.raises(IntegrityError):
            mca_session.flush()
        mca_session.rollback()

    def test_prediction_record_set_null_on_student_deletion(self, mca_session, base_hierarchy):
        """Verify SET NULL preserves prediction record when referenced student is deleted."""
        # Create an isolated student without registrations so student delete succeeds
        temp_student = MCAStudent(
            student_code="MCA-TEMP-001",
            session_id=base_hierarchy["academic_session"].id,
        )
        mca_session.add(temp_student)
        mca_session.flush()

        pred = MCAPredictionRecord(
            student_id=temp_student.id,
            registration_id=None,
            course_id=base_hierarchy["course"].id,
            predicted_tier="Good",
            model_name="mca_classifier_v1",
            input_snapshot_json={"attendance": 80.0},
            cutoff_timestamp=datetime.now(timezone.utc),
        )
        mca_session.add(pred)
        mca_session.commit()

        pred_id = pred.id
        # Delete temp_student
        mca_session.delete(temp_student)
        mca_session.commit()

        # Prediction record must still exist with student_id set to NULL
        refreshed_pred = mca_session.get(MCAPredictionRecord, pred_id)
        assert refreshed_pred is not None
        assert refreshed_pred.student_id is None
        assert refreshed_pred.predicted_tier == "Good"

    def test_prediction_record_set_null_on_registration_deletion(self, mca_session, base_hierarchy):
        """Verify SET NULL preserves prediction record when referenced registration is deleted."""
        # Create an isolated registration without snapshots so registration delete succeeds
        reg = MCACourseRegistration(
            student_id=base_hierarchy["student"].id,
            session_course_id=base_hierarchy["session_course"].id,
            semester_number=1,
            attempt_type="regular",
        )
        mca_session.add(reg)
        mca_session.commit()
        reg_id = reg.id

        pred = MCAPredictionRecord(
            student_id=None,
            registration_id=reg_id,
            course_id=base_hierarchy["course"].id,
            predicted_tier="Average",
            model_name="mca_classifier_v1",
            input_snapshot_json={"attendance": 70.0},
            cutoff_timestamp=datetime.now(timezone.utc),
        )
        mca_session.add(pred)
        mca_session.commit()
        pred_id = pred.id

        # Delete the registration (allowed since no snapshots reference it)
        mca_session.delete(reg)
        mca_session.commit()

        # Prediction record must still exist with registration_id set to NULL
        refreshed_pred = mca_session.get(MCAPredictionRecord, pred_id)
        assert refreshed_pred is not None
        assert refreshed_pred.registration_id is None
        assert refreshed_pred.predicted_tier == "Average"

    def test_soft_deactivation_fields_and_preservation(self, mca_session, base_hierarchy):
        """Verify student and registration soft-deactivation flags preserve history."""
        student = base_hierarchy["student"]
        reg = MCACourseRegistration(
            student_id=student.id,
            session_course_id=base_hierarchy["session_course"].id,
            semester_number=1,
            is_active=True,
        )
        mca_session.add(reg)
        mca_session.flush()

        snap = MCAAttendanceSnapshot(
            registration_id=reg.id,
            revision_number=1,
            attendance_percentage=88.5,
        )
        mca_session.add(snap)
        mca_session.commit()

        # Perform soft-deactivation
        student.is_active = False
        student.deactivated_at = datetime.now(timezone.utc)
        student.deactivation_reason = "Graduated / Transferred"

        reg.is_active = False

        mca_session.commit()

        # Verify all records remain fully queryable
        refreshed_student = mca_session.get(MCAStudent, student.id)
        assert refreshed_student.is_active is False
        assert refreshed_student.deactivation_reason == "Graduated / Transferred"
        assert len(refreshed_student.registrations) == 1
        assert refreshed_student.registrations[0].is_active is False
        assert len(refreshed_student.registrations[0].attendance_snapshots) == 1
        assert float(refreshed_student.registrations[0].attendance_snapshots[0].attendance_percentage) == 88.5
