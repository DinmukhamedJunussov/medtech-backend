# global configs
import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Загрузка .env файла из родительской директории
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_organization: str = os.getenv("OPENAI_ORGANIZATION", "")

    def __init__(self):
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY не найден в переменных окружения")
        if not self.openai_organization:
            logger.warning("OPENAI_ORGANIZATION не найден в переменных окружения")

settings = Settings()