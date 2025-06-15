#!/usr/bin/env python3
"""
Исправленный модуль для работы с базой данных Supabase
Решает проблему pgbouncer prepared statements
"""
import os
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import event, text
from loguru import logger

# Получение конфигурации базы данных из переменных окружения
supabase_url = os.getenv("SUPABASE_URL")

if not supabase_url:
    raise ValueError("SUPABASE_URL is required")

# Подготавливаем URL с параметрами для отключения prepared statements
database_url = supabase_url.replace("postgresql://", "postgresql+asyncpg://")

# Создание асинхронного движка для Supabase БЕЗ prepared statements
engine = create_async_engine(
    database_url,
    echo=False,  # Установите True для отладки SQL запросов
    future=True,
    poolclass=NullPool,  # Отключаем пул соединений - пусть pgbouncer управляет
    # Полностью отключаем кэширование
    execution_options={
        "compiled_cache": {},
        "autocommit": False
    },
    # Настройки для совместимости с pgbouncer в Supabase
    connect_args={
        "statement_cache_size": 0,  # Отключаем кэш prepared statements
        "command_timeout": 60,
        "server_settings": {
            "jit": "off",  # Отключаем JIT
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

# База для моделей
Base = declarative_base()

# Хук для отключения prepared statements на уровне соединения
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Устанавливаем параметры для отключения prepared statements"""
    try:
        # Для asyncpg это не применимо, но сохраняем структуру
        pass
    except Exception as e:
        logger.warning(f"Could not set connection parameters: {e}")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """Инициализация базы данных - создание таблиц"""
    try:
        # Используем простое соединение без кэширования для инициализации
        simple_engine = create_async_engine(
            database_url,
            echo=False,
            poolclass=NullPool,
            connect_args={
                "statement_cache_size": 0,
                "command_timeout": 60
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

async def test_connection() -> bool:
    """Тестирует соединение с базой данных"""
    try:
        async with AsyncSessionLocal() as session:
            # Простой тест соединения
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("Database connection test successful")
                return True
            else:
                logger.error("Database connection test failed - unexpected result")
                return False
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

# Экспортируем для совместимости
__all__ = [
    "engine",
    "AsyncSessionLocal", 
    "Base",
    "get_db",
    "init_db",
    "test_connection"
] 