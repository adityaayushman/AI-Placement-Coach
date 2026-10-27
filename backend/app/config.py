from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", protected_namespaces=("settings_",)
    )

    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-real-deployments"
    cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://placement:placement@localhost:5432/placement"
    redis_url: str = "redis://localhost:6379/0"
    storage_dir: str = "./storage"
    model_dir: str = "./models"

    access_token_minutes: int = 15
    refresh_token_days: int = 7
    # Run background jobs in-process instead of via RQ (tests, single-box demos).
    jobs_inline: bool = False
    upload_max_mb: int = 5
    # Rows generated when no readiness model exists yet (synthetic bootstrap model).
    synthetic_rows: int = 1500
    auth_rate_limit_per_minute: int = 20
    # Optional heavy backends; used only when the package is installed.
    use_sentence_transformers: bool = False
    use_faster_whisper: bool = False
    use_dkt: bool = False

    admin_email: str = ""
    admin_password: str = ""

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        # Render (and Heroku-style hosts) hand out postgres:// URLs.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix) :]
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
