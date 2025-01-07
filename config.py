"""
Конфигурация проекта с использованием Pydantic для валидации.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Основные настройки приложения."""
    
    # Настройки бота
    BOT_TOKEN: str
    ADMIN_IDS: List[int] = Field(default_factory=list)

    # Настройки PostgreSQL
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    @property
    def database_url(self) -> str:
        """Получить URL для подключения к базе данных."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Настройки Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str

    @property
    def redis_url(self) -> str:
        """Получить URL для подключения к Redis."""
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Настройки парсера
    PARSER_INTERVAL: int = 600  # 10 минут
    CACHE_TTL: int = 300  # 5 минут

    # Настройки Selenium
    CHROME_DRIVER_PATH: str
    HEADLESS: bool = True

    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @validator("ADMIN_IDS", pre=True)
    def parse_admin_ids(cls, v: str | List[int]) -> List[int]:
        """Преобразование строки с ID администраторов в список целых чисел."""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Создание экземпляра конфигурации
config = Settings()