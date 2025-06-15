"""
Главный файл FastAPI приложения - рефакторинг
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from mangum import Mangum

from app.routers import endpoints
from app.middlewares import monitor_service
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Управление жизненным циклом приложения"""
    logger.info("MedTech API starting up...")
    
    # Инициализация базы данных
    try:
        from app.database import init_db
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        # Не останавливаем приложение, если БД недоступна
        logger.warning("Приложение продолжит работу без базы данных")
    
    # Инициализация сервисов
    try:
        # from app.services.postgres import postgres_service, PostgresService
        from app.services.llm import llm_service, LLMService
        from app.services.qdrant import qdrant_service
        
        # # Инициализация PostgreSQL сервиса
        # if postgres_service is None:
        #     postgres_service = PostgresService(str(settings.pg_dsn))
        #     await postgres_service.connect()
        
      
        # Инициализация Qdrant сервиса
        await qdrant_service.connect()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
    
    yield
    
    # Закрытие соединений
    logger.info("MedTech API shutting down...")
    try:
        from app.database import close_db
        await close_db()
        
        # if postgres_service:
        #     await postgres_service.close()
        
        await qdrant_service.close()
        
        logger.info("All connections closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Создает и настраивает FastAPI приложение"""
    
    app = FastAPI(
        title="MedTech API",
        description="API для анализа результатов анализа крови",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # Настройка CORS
    setup_cors(app)
    
    # Добавление middleware
    app.middleware("http")(monitor_service)
    
    # Подключение роутеров
    app.include_router(endpoints.router)
    
    return app


def setup_cors(app: FastAPI) -> None:
    """Настраивает CORS для приложения"""
    origins = [
        "*",
        "http://localhost:3000",
        "https://localhost:3000",
        "http://medtech-frontend.vercel.app",
        "https://medtech-frontend.vercel.app",
        "http://www.oncotest.kz",
        "https://www.oncotest.kz",
        "http://oncotest.kz",
        "https://oncotest.kz",
        "http://api.oncotest.kz",
        "https://api.oncotest.kz",
        "https://preview--health-score-reveal.lovable.app",
        "https://health-score-reveal.lovable.app",
        "http://medtech-backend-alb-988383858.us-east-1.elb.amazonaws.com",
        "https://medtech-backend-alb-988383858.us-east-1.elb.amazonaws.com"
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Создаем приложение
app = create_app()

# Обработчик для AWS Lambda
handler = Mangum(app) 