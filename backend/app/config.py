from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "VisemePal API"
    debug: bool = True
    database_url: str = f"sqlite:///{BACKEND_DIR / 'var' / 'visemepal.db'}"
    upload_dir: Path = BACKEND_DIR / "uploads"
    max_upload_bytes: int = 10 * 1024 * 1024
    min_audio_duration_ms: int = 300
    min_audio_rms: int = 80
    upload_retention_days: int = 30

    ise_app_id: str = ""
    ise_api_key: str = ""
    ise_api_secret: str = ""

    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-flash"

    ise_host: str = "ise-api.xfyun.cn"
    ise_path: str = "/v2/open-ise"
    error_score_threshold: float = 70.0

    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
(BACKEND_DIR / "var").mkdir(parents=True, exist_ok=True)
