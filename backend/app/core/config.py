from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Attendance System"
    database_url: str = "sqlite:///./attendance.db"
    secret_key: str = "change-me-before-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "attendance-storage"
    minio_secure: bool = False

    # Face recognition
    face_similarity_threshold: float = 0.60

    # AI reports
    hf_model_name: str = "Qwen/Qwen2.5-3B-Instruct"
    hf_max_new_tokens: int = 220
    ai_enable_local_model: bool = False

    # Email automation
    email_from: str = "attendai@example.local"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    hod_email: str = "hod@example.local"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_database_url(self) -> str:
        url = self.database_url
        if url.startswith("sqlite:///./"):
            backend_dir = Path(__file__).resolve().parents[2]
            db_name = url.split("sqlite:///./")[1]
            return f"sqlite:///{backend_dir}/{db_name}".replace("\\", "/")
        elif url.startswith("sqlite:///"):
            backend_dir = Path(__file__).resolve().parents[2]
            db_name = url.split("sqlite:///")[1]
            if not db_name.startswith("/") and not (len(db_name) > 1 and db_name[1] == ":"):
                return f"sqlite:///{backend_dir}/{db_name}".replace("\\", "/")
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
