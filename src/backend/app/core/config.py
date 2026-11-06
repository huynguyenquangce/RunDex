from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rundex:rundex_dev@localhost:5432/rundex"
    # Working files of the ingestion pipeline: data/inbox (pages to extract), data/outbox (results).
    # Candidates at or above this confidence from an official source may be applied automatically.
    ingest_auto_threshold: float = 0.85
    ingest_data_dir: Path = Path(__file__).resolve().parents[2] / "data"


settings = Settings()
