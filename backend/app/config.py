"""
backend/app/config.py

Application settings loaded from environment variables.

All sensitive values (database credentials, etc.) must be placed
in a .env file in the backend/ directory. That file is gitignored
and must never be committed to version control.

Usage anywhere in the app:
    from app.config import settings
    print(settings.safe_database_url)
"""

import os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load variables from backend/.env (if it exists) into os.environ.
# This has no effect when the file does not exist, so the app can
# also be configured via real environment variables in production.
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.is_file():
    load_dotenv(dotenv_path=_env_path)
else:
    load_dotenv()



class Settings:
    """Central place for all application configuration."""

    def __init__(self) -> None:
        # Database settings
        self.db_host: str = os.getenv("DB_HOST", "localhost")
        try:
            self.db_port: int = int(os.getenv("DB_PORT", "3306"))
        except (ValueError, TypeError):
            self.db_port: int = 3306

        self.db_name: str = os.getenv("DB_NAME", "student_performance_db")
        self.db_user: str = os.getenv("DB_USER", "root")
        self.db_password: str = os.getenv("DB_PASSWORD", "")

        # Application environment: 'development', 'testing', or 'production'
        self.app_env: str = os.getenv("APP_ENV", "development")

        # CORS — which origins are allowed to call this API
        dev_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ]
        raw_cors = os.getenv("CORS_ORIGINS", "")
        origins_set: set[str] = set()
        if raw_cors.strip():
            for origin in raw_cors.split(","):
                cleaned = origin.strip().rstrip("/")
                if cleaned:
                    origins_set.add(cleaned)

        # In development mode, guarantee that both localhost and 127.0.0.1 on ports 5173/5174 are always allowed
        if self.app_env == "development" or not origins_set:
            for dev_orig in dev_origins:
                origins_set.add(dev_orig)

        self.cors_origins: list[str] = sorted(list(origins_set))

    @property
    def database_url(self) -> str:
        """
        Build the SQLAlchemy connection URL.
        
        If a direct DATABASE_URL is set in environment (e.g. for testing with SQLite
        or custom connection strings), it takes precedence.
        Otherwise, builds the URL from individual DB_* settings using PyMySQL driver.
        Format: mysql+pymysql://user:password@host:port/dbname
        """
        custom_url = os.getenv("DATABASE_URL")
        if custom_url:
            return custom_url

        # URL-encode username and password to handle special characters (@, :, /, etc.)
        encoded_user = urllib.parse.quote_plus(self.db_user)
        encoded_password = urllib.parse.quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def safe_database_url(self) -> str:
        """
        Return the database connection URL with credentials masked.
        Safe to log, print, or expose in diagnostic endpoints without leaking secrets.
        """
        raw_url = self.database_url
        if "@" in raw_url and "://" in raw_url:
            prefix, rest = raw_url.split("://", 1)
            creds, location = rest.split("@", 1)
            user = creds.split(":", 1)[0] if ":" in creds else creds
            return f"{prefix}://{user}:***@{location}"
        return raw_url


# Single shared instance — import this throughout the application
settings = Settings()
