"""
Схемы для работы с документами и LlamaIndex
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Метаданные документа"""
    filename: str = Field(..., description="Имя файла")
    content_type: Optional[str] = Field(None, description="Тип контента")
    num_pages: int = Field(..., description="Количество страниц")
    text_length: int = Field(..., description="Длина текста")
    summary: str = Field(..., description="Краткое резюме документа")


class ParsedDocument(BaseModel):
    """Схема для парсинга документа"""
    content: str = Field(..., description="Извлеченный текст из документа")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные документа")
    page_count: Optional[int] = Field(None, description="Количество страниц")
    file_size: Optional[int] = Field(None, description="Размер файла в байтах")
    processing_time: Optional[float] = Field(None, description="Время обработки в секундах")


class DocumentQuery(BaseModel):
    """Схема для запроса к документам"""
    documents: List[str] = Field(..., description="Список текстов документов для поиска")
    query: str = Field(..., description="Поисковый запрос")


class SourceNode(BaseModel):
    """Исходный узел с информацией о релевантности"""
    text: str = Field(..., description="Текст узла")
    score: Optional[float] = Field(None, description="Оценка релевантности")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные узла")


class DocumentQueryResponse(BaseModel):
    """Схема ответа на запрос к документу"""
    answer: str = Field(..., description="Ответ на запрос")
    sources: List[str] = Field(default_factory=list, description="Источники информации")
    confidence: Optional[float] = Field(None, description="Уверенность в ответе (0-1)")
    context: Optional[str] = Field(None, description="Контекст, использованный для ответа")


class ProcessedBloodTestDocument(BaseModel):
    """Схема для обработанного документа с анализом крови"""
    # Информация о документе
    filename: str = Field(..., description="Имя файла")
    content: str = Field(..., description="Извлеченный текст")
    
    # Информация о сохранении в базе данных
    session_id: str = Field(..., description="ID сессии анализа")
    blood_test_record_id: Optional[int] = Field(None, description="ID записи анализа крови в БД")
    
    # Статус обработки
    processing_status: str = Field(..., description="Статус обработки")
    
    # Извлеченные данные анализа крови (если удалось распарсить)
    blood_test_data: Optional[Dict[str, Any]] = Field(None, description="Данные анализа крови")
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Время создания")
    file_size: Optional[int] = Field(None, description="Размер файла")
    processing_time: Optional[float] = Field(None, description="Время обработки") 