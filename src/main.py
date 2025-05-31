"""
Главный файл FastAPI приложения - рефакторинг
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from mangum import Mangum

from src.api.endpoints import router
from src.middlewares import monitor_service
from src.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Управление жизненным циклом приложения"""
    logger.info("MedTech API starting up...")
    yield
    logger.info("MedTech API shutting down...")


def create_app() -> FastAPI:
    """Создает и настраивает FastAPI приложение"""
    
    app = FastAPI(
        title="MedTech API",
        description="API для анализа результатов анализа крови и расчета SII индекса",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # Настройка CORS
    setup_cors(app)
    
    # Добавление middleware
    app.middleware("http")(monitor_service)
    
    # Подключение роутеров
    app.include_router(router)
    
    return app


def setup_cors(app: FastAPI) -> None:
    """Настраивает CORS для приложения"""
    origins = [
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
