"""
Сервис для парсинга PDF документов с помощью LlamaIndex
"""
import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import UploadFile, HTTPException
from loguru import logger
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.readers.file import PDFReader

from app.settings import settings


class LlamaIndexService:
    """Сервис для работы с LlamaIndex для парсинга PDF документов"""
    
    def __init__(self):
        """Инициализация сервиса LlamaIndex"""
        self.openai_api_key = settings.openai_api_key
        if not self.openai_api_key:
            raise ValueError("OpenAI API key не найден в настройках")
        
        # Настройка LlamaIndex
        Settings.llm = OpenAI(
            api_key=self.openai_api_key,
            model="gpt-4o-mini",
            temperature=0.1,
        )
        Settings.embed_model = OpenAIEmbedding(
            api_key=self.openai_api_key,
            model="text-embedding-3-small"
        )
        Settings.node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
        
        logger.info("LlamaIndex сервис инициализирован")
    
    async def parse_pdf_document(self, file: UploadFile) -> Dict[str, Any]:
        """
        Парсит PDF документ с помощью LlamaIndex
        
        Args:
            file: Загруженный PDF файл
            
        Returns:
            Dict с извлеченным текстом и метаданными
        """
        try:
            # Проверяем тип файла
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400, 
                    detail="Поддерживаются только PDF файлы"
                )
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                # Загружаем документ с помощью LlamaIndex
                pdf_reader = PDFReader()
                documents = pdf_reader.load_data(Path(tmp_file_path))
                
                if not documents:
                    raise HTTPException(
                        status_code=422,
                        detail="Не удалось извлечь текст из PDF файла"
                    )
                
                # Объединяем весь текст
                full_text = "\n".join([doc.text for doc in documents])
                
                # Создаем индекс для семантического поиска
                index = VectorStoreIndex.from_documents(documents)
                query_engine = index.as_query_engine()
                
                # Извлекаем основную информацию о документе
                metadata = {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "num_pages": len(documents),
                    "text_length": len(full_text),
                    "summary": await self._generate_summary(query_engine, full_text[:2000])
                }
                
                logger.info(f"Успешно обработан PDF файл: {file.filename}")
                
                return {
                    "text": full_text,
                    "metadata": metadata,
                    "documents": [{"text": doc.text, "metadata": doc.metadata} for doc in documents],
                    "query_engine_available": True
                }
                
            finally:
                # Удаляем временный файл
                os.unlink(tmp_file_path)
                
        except Exception as e:
            logger.error(f"Ошибка при парсинге PDF файла {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка обработки файла: {str(e)}"
            )
    
    async def _generate_summary(self, query_engine, text_sample: str) -> str:
        """
        Генерирует краткое резюме документа
        
        Args:
            query_engine: Query engine от LlamaIndex
            text_sample: Образец текста для анализа
            
        Returns:
            Краткое резюме документа
        """
        try:
            summary_prompt = (
                "Проанализируй этот документ и предоставь краткое резюме на русском языке. "
                "Опиши основную тему, ключевые моменты и тип документа. "
                "Максимум 3-4 предложения."
            )
            
            response = query_engine.query(summary_prompt)
            return str(response)
            
        except Exception as e:
            logger.warning(f"Не удалось сгенерировать резюме: {str(e)}")
            return "Резюме недоступно"
    
    async def query_document(
        self, 
        documents: list, 
        query: str
    ) -> Dict[str, Any]:
        """
        Выполняет запрос к документу
        
        Args:
            documents: Список документов от LlamaIndex
            query: Запрос пользователя
            
        Returns:
            Ответ на запрос с контекстом
        """
        try:
            # Создаем индекс из документов
            from llama_index.core import Document
            
            docs = [Document(text=doc["text"], metadata=doc["metadata"]) for doc in documents]
            index = VectorStoreIndex.from_documents(docs)
            query_engine = index.as_query_engine(
                response_mode="compact",
                similarity_top_k=3
            )
            
            # Выполняем запрос
            response = query_engine.query(query)
            
            return {
                "query": query,
                "response": str(response),
                "source_nodes": [
                    {
                        "text": node.text,
                        "score": node.score,
                        "metadata": node.metadata
                    }
                    for node in response.source_nodes
                ] if hasattr(response, 'source_nodes') else []
            }
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка выполнения запроса: {str(e)}"
            )


# Глобальный экземпляр сервиса
llamaindex_service: Optional[LlamaIndexService] = None

def get_llamaindex_service() -> LlamaIndexService:
    """Получает экземпляр LlamaIndex сервиса"""
    global llamaindex_service
    if llamaindex_service is None:
        llamaindex_service = LlamaIndexService()
    return llamaindex_service 