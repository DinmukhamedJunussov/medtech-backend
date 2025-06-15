from typing import Annotated
from pydantic import Field, HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )

    port: Annotated[int, Field(default=8000)]
    app_secret: Annotated[str, Field(default="default_secret_key_please_change_in_production", min_length=32)]
    openai_organization: Annotated[str, Field(alias="OPENAI_ORGANIZATION", default="")]
    openai_api_key: Annotated[str, Field(alias="OPENAI_API_KEY", default="")]
    pg_dsn: Annotated[
        PostgresDsn,
        Field(
            alias="DATABASE_URL",
            default="postgres://user:pass@localhost:5432/database",
        ),
    ]
    cors_whitelist_domains: Annotated[
        set[HttpUrl],
        Field(alias="CORS_WHITELIST", default=["http://localhost:3000"]),
    ]


settings = AppSettings()
