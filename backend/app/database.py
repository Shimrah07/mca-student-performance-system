"""
backend/app/database.py

SQLAlchemy engine, session management, and database lifecycle utilities.

Architecture:
- Defines the DeclarativeBase (Base) used by all ORM models.
- Creates the SQLAlchemy engine with pool_pre_ping for MySQL resilience.
- Provides SessionLocal for generating database sessions.
- Exposes `get_db()` dependency for FastAPI route handlers with automatic cleanup.
- Provides `init_db()` for non-destructive table creation.
- Provides `check_db_connection()` for safe connectivity checks with credential masking.
"""

from typing import Generator
from sqlalchemy import create_engine, text, CheckConstraint
from sqlalchemy.engine import Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import settings

# ---------------------------------------------------------------------------
# MySQL Dialect DDL Overrides
# ---------------------------------------------------------------------------
@compiles(CheckConstraint, "mysql")
def _compile_check_constraint_mysql(element, compiler, **kw):
    """
    MySQL 8.0+ disallows CHECK constraints referencing AUTO_INCREMENT columns
    (Error 3818: Check constraint cannot refer to an auto-increment column).
    Omit ck_mca_assessment_event_no_self_ref from MySQL DDL while retaining
    it for SQLite and other compliant database engines.
    """
    if element.name == "ck_mca_assessment_event_no_self_ref":
        return None
    return compiler.visit_check_constraint(element, **kw)

# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------------------------
# Engine Creation Factory
# ---------------------------------------------------------------------------
def get_engine(db_url: str | None = None, echo: bool = False) -> Engine:
    """
    Create a SQLAlchemy Engine with settings appropriate for the database dialect.

    - For SQLite (typically used during automated tests):
      enables `check_same_thread: False`.
    - For MySQL (production / development):
      enables `pool_pre_ping=True` (detects stale dropped connections) and
      `pool_recycle=3600` (recycles connections before MySQL timeout).
    """
    url = db_url or settings.database_url
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=echo,
        )

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=echo,
    )


# Default application engine & sessionmaker
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# FastAPI Session Dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and guarantees closure.

    Usage in routers:
        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Database Initialization & Safety
# ---------------------------------------------------------------------------
MCA_TABLE_ALLOWLIST = (
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
)


def init_db(target_engine: Engine | None = None, mca_only: bool = False) -> None:
    """
    Create tables defined in Base metadata if they do not already exist.

    Args:
        target_engine: Optional SQLAlchemy Engine to bind. Defaults to application engine.
        mca_only: If True, creates strictly and exclusively the 13 approved MCA tables
                  defined in MCA_TABLE_ALLOWLIST. If False (default), creates all registered tables.

    Safety:
    - This operation is strictly NON-DESTRUCTIVE: `create_all` inspects the
      database and only issues `CREATE TABLE IF NOT EXISTS`.
    - It NEVER drops, truncates, or modifies existing tables or data.
    """
    # Import models here to ensure they are registered with Base metadata
    import app.models  # noqa: F401

    target = target_engine or engine

    if mca_only:
        # Verify all 13 approved MCA tables exist in metadata before calling create_all
        missing_tables = [tbl for tbl in MCA_TABLE_ALLOWLIST if tbl not in Base.metadata.tables]
        if missing_tables:
            raise RuntimeError(
                f"Cannot initialize MCA database: The following approved MCA tables are missing "
                f"from SQLAlchemy Base metadata: {missing_tables}"
            )
        mca_tables = [Base.metadata.tables[tbl] for tbl in MCA_TABLE_ALLOWLIST]
        Base.metadata.create_all(bind=target, tables=mca_tables)
    else:
        Base.metadata.create_all(bind=target)


def check_db_connection(target_engine: Engine | None = None) -> tuple[bool, str]:
    """
    Safely verify database connectivity by executing a lightweight query.

    Security:
    - Returns a boolean status and a descriptive message.
    - Masks any passwords or raw connection strings to prevent credential leaks.

    Returns:
        (True, "Database connection successful") or
        (False, "Database connection failed: <sanitized details>")
    """
    target = target_engine or engine
    try:
        with target.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connection successful"
    except Exception as exc:
        raw_error = str(exc)
        # Security sanitization: strip any occurrences of the configured password
        if settings.db_password and settings.db_password in raw_error:
            raw_error = raw_error.replace(settings.db_password, "***")
        return False, f"Database connection failed: {raw_error}"
