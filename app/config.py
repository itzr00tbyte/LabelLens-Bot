from typing import List, Optional
import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    TELEGRAM_BOT_TOKEN: str = ""
    ADMIN_TELEGRAM_IDS: List[int] = []
    DATABASE_URL: str = "sqlite+aiosqlite:///./bot.db"

    TESSERACT_CMD: Optional[str] = None
    MAX_UPLOAD_MB: int = 10
    MIN_TEMPLATE_CONFIDENCE: float = 0.50
    LOW_CONFIDENCE_THRESHOLD: float = 0.50

    STORE_ORIGINAL_IMAGES: bool = False
    STORE_OCR_TEXT: bool = True
    TEMP_FILE_RETENTION_MINUTES: int = 15

    RATE_LIMIT_UPLOADS_PER_MINUTE: int = 5
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    TEMPLATES_DIR: str = "app/templates/documents"

    @field_validator("ADMIN_TELEGRAM_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: object) -> List[int]:
        if isinstance(v, str):
            v = v.strip().strip("[]")
            if not v:
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip().lstrip("-").isdigit()]
        if isinstance(v, list):
            return [int(x) for x in v]
        if isinstance(v, int):
            return [v]
        return []

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


settings = Settings()
