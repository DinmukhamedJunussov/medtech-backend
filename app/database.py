# """
# Конфигурация базы данных
# """
# from typing import AsyncGenerator
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
# from sqlalchemy.orm import DeclarativeBase
# from loguru import logger

# from app.settings import settings


# class Base(DeclarativeBase):
#     """Базовый класс для всех моделей SQLAlchemy"""
#     pass


# # Создание асинхронного движка
# engine = create_async_engine(
#     str(settings.pg_dsn).replace("postgresql://", "postgresql+asyncpg://"),
#     echo=False,  # Установите True для отладки SQL запросов
#     future=True
# )

# # Создание фабрики сессий
# AsyncSessionLocal = async_sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False
# )


# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     """
#     Dependency для получения сессии базы данных
    
#     Yields:
#         AsyncSession: Сессия базы данных
#     """
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#         except Exception as e:
#             logger.error(f"Database session error: {e}")
#             await session.rollback()
#             raise
#         finally:
#             await session.close()


# async def init_db() -> None:
#     """Инициализация базы данных - создание таблиц"""
#     try:
#         async with engine.begin() as conn:
#             # Создаем все таблицы
#             await conn.run_sync(Base.metadata.create_all)
#         logger.info("Database tables created successfully")
#     except Exception as e:
#         logger.error(f"Failed to initialize database: {e}")
#         raise


# async def close_db() -> None:
#     """Закрытие соединений с базой данных"""
#     try:
#         await engine.dispose()
#         logger.info("Database connections closed")
#     except Exception as e:
#         logger.error(f"Error closing database connections: {e}")
#         raise 