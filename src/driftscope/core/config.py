"""Pydantic Settings v2 — ładuje konfigurację z .env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    base_seed: int = 42
    scraper_user_agent: str = "DriftScope/0.1"
    scraper_request_timeout_sec: int = 30
    scraper_rate_limit_delay_sec: float = 2.0
    artifacts_dir: Path = Path("./artifacts")
    data_seed_path: Path = Path("./data/seed/eurojackpot_history.csv")
    log_level: str = "INFO"
    lotto_api_key: str = ""


settings = Settings()
