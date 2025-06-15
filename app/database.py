"""
Конфигурация базы данных
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger
import os

from app.settings import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy"""
    pass


# Получаем URL Supabase из переменных окружения
supabase_url = os.getenv("SUPABASE_URL")
if not supabase_url:
    logger.error("SUPABASE_URL не найден в переменных окружения!")
    raise ValueError("SUPABASE_URL is required")

# Подготавливаем URL с параметрами для отключения prepared statements
database_url = supabase_url.replace("postgresql://", "postgresql+asyncpg://")
if "?" in database_url:
    database_url += "&prepared_statement_cache_size=0&statement_cache_size=0"
else:
    database_url += "?prepared_statement_cache_size=0&statement_cache_size=0"

# Создание асинхронного движка для Supabase с полным отключением prepared statements  
engine = create_async_engine(
    database_url,
    echo=False,  # Установите True для отладки SQL запросов
    future=True,
    pool_pre_ping=True,  # Проверяем соединение перед использованием
    # Отключаем prepared statements
    execution_options={
        'compiled_cache': None,
        'autocommit': False
    },
    # Настройки для совместимости с pgbouncer в Supabase
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "command_timeout": 60,
        "server_settings": {
            "jit": "off",  # Отключаем JIT компиляцию для стабильности
            "plan_cache_mode": "off"  # Отключаем кэш планов
        }
    }
)

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии базы данных
    
    Yields:
        AsyncSession: Сессия базы данных
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Инициализация базы данных - создание таблиц"""
    try:
        # Используем простое соединение без prepared statements для инициализации
        simple_engine = create_async_engine(
            database_url,
            echo=False,
            isolation_level="AUTOCOMMIT",
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0
            }
        )
        
        async with simple_engine.begin() as conn:
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
        
        await simple_engine.dispose()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.info("Continuing without table creation - tables may already exist")
        # Не прерываем работу, таблицы могут уже существовать


async def close_db() -> None:
    """Закрытие соединений с базой данных"""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise 