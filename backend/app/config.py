"""
backend/app/config.py

Application settings loaded from environment variables.

All sensitive values (database credentials, etc.) must be placed
in a .env file in the backend/ directory.  That file is gitignored
and must never be committed to version control.

Usage anywhere in the app:
    from app.config import settings
    print(settings.db_host)
"""

import os
from dotenv import load_dotenv

# Load variables from backend/.env (if it exists) into os.environ.
# This has no effect when the file does not exist, so the app can
# also be configured via real environment variables in production.
load_dotenv()


class Settings:
    """Central place for all application configuration."""

    # Database
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "student_performance_db")
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")  # Must be set in .env

    # Application
    app_env: str = os.getenv("APP_ENV", "development")

    # CORS — which origins are allowed to call this API
    # In development this is the Vite dev server; in production it is the
    # deployed frontend URL.
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")

    @property
    def database_url(self) -> str:
        """
        Build the SQLAlchemy connection URL from individual settings.
        Format: mysql+pymysql://user:password@host:port/dbname
        This is used by database.py to create the engine.
        """
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# Single shared instance — import this throughout the application
settings = Settings()
