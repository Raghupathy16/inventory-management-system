"""
Application configuration.

CONCEPT: Environment-based configuration
-----------------------------------------
What it is: instead of hardcoding values like database passwords or secret
keys into the source code, we read them from environment variables at
startup.

Why we need it: secrets committed to source control are a security
liability (they end up in git history forever, visible to anyone with repo
access). Config also differs between environments (local dev vs. Docker vs.
a future production server) — hardcoding would mean editing source code
every time we switch environments.

Where we use it: every place that needs a secret or an environment-specific
value (DB credentials, JWT secret key, token expiry) reads it from this
`Settings` object instead of a literal string.

What problem it solves: it separates "config" from "code." The same code
can run in different environments just by supplying different environment
variables — no code changes required.

We use `pydantic-settings` (built on Pydantic) instead of plain
`os.environ.get(...)` calls because it gives us:
  1. Type validation — e.g. DB_PORT must actually be an int, not any string.
  2. Fail-fast startup — if a required variable is missing, the app refuses
     to start with a clear error, instead of failing mysteriously later.
  3. A single, discoverable source of truth for "what config does this app
     need?" (this file).
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

class Settings(BaseSettings):
    # --- App metadata ---
    APP_NAME: str = "Inventory & Procurement Management System"
    ENVIRONMENT: str = "development"  # development | testing | production
    DEBUG: bool = True

    # --- Database ---
    DB_HOST: str
    DB_PORT: int = 3306
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # --- Security (used starting Phase 3, defined here already so the
    #     shape of config is stable from the start) ---
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def database_url(self) -> str:
       return URL.create(
          drivername="mysql+pymysql",
          username=self.DB_USER,
          password=self.DB_PASSWORD,
         host=self.DB_HOST,
         port=self.DB_PORT,
         database=self.DB_NAME,
     ).render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    CONCEPT: Dependency Injection (a first, simple example)
    ---------------------------------------------------------
    What it is: rather than every module creating its own `Settings()`
    instance (which would each re-read and re-validate environment
    variables), other parts of the app *receive* the settings object
    through a function call. FastAPI will later inject this via
    `Depends(get_settings)` in routes/services that need it.

    Why we need it: it decouples "who needs config" from "how config is
    loaded." If we ever change how settings are constructed, only this
    function changes.

    Where we use it: `app/db/database.py` (to build the engine),
    `app/core/security.py` (Phase 3, for JWT secret), and any service that
    needs environment-aware behavior.

    `lru_cache` ensures `Settings()` — which parses and validates every env
    var — only runs once per process, not on every call.
    """
    return Settings()
