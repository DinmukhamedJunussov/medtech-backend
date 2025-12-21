"""
API эндпоинты для MedTech приложения
"""
import json
import os
from typing import Dict, Any, Union
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import time

from app.core.exceptions import handle_medtech_exception, MedTechException
from app.schemas.blood_results import BloodTestResults, SIIResult, ParsedBloodTestResponse, AnalyteResult
from app.schemas.document_schemas import ParsedDocument, DocumentQuery, DocumentQueryResponse, ProcessedBloodTestDocument
from app.schemas.user_uploads import BloodTestResults as BloodTestResultsSchema
from app.services.document_processor import DocumentProcessor
from app.services.sii_calculator import SIICalculator
from app.services.llamaindex_service import get_llamaindex_service
from app.services.database_service import get_database_service
from app.services.normalized_database_service import get_normalized_database_service
from app.database import get_db
from typing import List
from app.utils.const import nazvaniya_analizov, nazvaniya_mapping
from openai import OpenAI
from llama_parse import LlamaParse

router = APIRouter()

# Инициализируем сервисы
document_processor = DocumentProcessor()
sii_calculator = SIICalculator()


@router.get("/")
def read_root():
    """Корневой эндпоинт"""
    return {
        "message": "MedTech API",
        "version": "2.0",
        "description": "API для анализа результатов анализа крови"
    }


@router.post("/v3/blood-tests/upload-multiple-files", response_model=ParsedBloodTestResponse)
async def parse_blood_test_v2(
    files: List[UploadFile] = File(...)
) -> ParsedBloodTestResponse:
    """
    Parse blood test PDF files using LlamaParse + OpenAI.
    
    Args:
        files: List of uploaded PDF/image files with blood test results
        
    Returns:
        ParsedBloodTestResponse: Structured blood test data with patient info and analyte values
    """
    # Validate API keys
    if not os.getenv("LLAMA_CLOUD_API_KEY"):
        raise HTTPException(status_code=500, detail="LLAMA_CLOUD_API_KEY is not set")

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    # Step 1: Parse all PDFs with LlamaParse
    contents = ""
    parser = LlamaParse(result_type="text", language='ru')
    
    for file in files:
        logger.info(f"Processing file: {file.filename}")
        file_content = await file.read()
        
        documents = await parser.aparse(file_content, extra_info={"file_name": file.filename})
        text_docs = documents.get_text_documents()
        
        if text_docs:
            contents += text_docs[0].text + "\n\n"
    
    # Debug: save parsed content
    with open("parsed_blood_test_contents.txt", "w", encoding="utf-8") as f:
        f.write(contents)

    # Step 2: Extract data with OpenAI (using JSON mode)
    system_prompt = """You are a medical laboratory data extraction specialist. Your task is to parse blood test results from clinical documents and extract numeric values with their reference ranges.

IMPORTANT PARSING RULES:
1. Values like "HGB 174 г/л" mean the value is 174
2. Values like "WBC 6,13 *10^9/л" mean the value is 6.13 (note: comma is decimal separator)
3. Values like "NEU% 41,0 %" mean the value is 41.0
4. Reference ranges like "130 - 160" should be kept as string "130 - 160"
5. If a test row has no value (empty), set value to null
6. Calculate age from birth date if not directly provided

Return a valid JSON object. Use ENGLISH keys as specified."""

    user_prompt = f"""Extract blood test data from this clinical document.

DOCUMENT:
{contents}

REQUIRED OUTPUT FORMAT (use these EXACT English field names):
{{
    "full_name": "<patient full name>",
    "age": <integer age>,
    "sex": "Мужской" or "Женский",
    "date": "<test date in DD.MM.YYYY>",
    "hemoglobin": {{"value": <number>, "ref": "<range>"}},
    "erythrocytes": {{"value": <number>, "ref": "<range>"}},
    "hematocrit": {{"value": <number>, "ref": "<range>"}},
    "mcv": {{"value": <number>, "ref": "<range>"}},
    "mch": {{"value": <number>, "ref": "<range>"}},
    "mchc": {{"value": <number>, "ref": "<range>"}},
    "rdw": {{"value": <number>, "ref": "<range>"}},
    "platelets": {{"value": <number>, "ref": "<range>"}},
    "wbc": {{"value": <number>, "ref": "<range>"}},
    "neutrophils": {{"value": <number>, "ref": "<range>"}},
    "neutrophils_abs": {{"value": <number>, "ref": "<range>"}},
    "lymphocytes": {{"value": <number>, "ref": "<range>"}},
    "lymphocytes_abs": {{"value": <number>, "ref": "<range>"}},
    "monocytes": {{"value": <number>, "ref": "<range>"}},
    "monocytes_abs": {{"value": <number>, "ref": "<range>"}},
    "eosinophils": {{"value": <number>, "ref": "<range>"}},
    "eosinophils_abs": {{"value": <number>, "ref": "<range>"}},
    "basophils": {{"value": <number>, "ref": "<range>"}},
    "basophils_abs": {{"value": <number>, "ref": "<range>"}},
    "esr": {{"value": <number or null>, "ref": "<range>"}},
    "thrombocrit": {{"value": <number>, "ref": "<range>"}},
    "mpv": {{"value": <number>, "ref": "<range>"}},
    "glucose": {{"value": <number or null>, "ref": "<range or null>"}},
    "cholesterol": {{"value": <number or null>, "ref": "<range or null>"}},
    "hdl_cholesterol": {{"value": <number or null>, "ref": "<range or null>"}},
    "ldl_cholesterol": {{"value": <number or null>, "ref": "<range or null>"}},
    "triglycerides": {{"value": <number or null>, "ref": "<range or null>"}},
    "creatinine": {{"value": <number or null>, "ref": "<range or null>"}}
}}

MAPPING from Russian document to English keys:
- Гемоглобин → hemoglobin
- Эритроциты → erythrocytes  
- Гематокрит → hematocrit
- Средний объем эритроцита / MCV → mcv
- Среднее содержание Hb в эритроците / MCH → mch
- Средняя концентрация Hb в эритроците / MCHC → mchc
- Распределение эритроцитов по объему / RDW → rdw
- Тромбоциты → platelets
- Лейкоциты → wbc
- Нейтрофилы (%) → neutrophils
- Нейтрофилы (абс.) → neutrophils_abs
- Лимфоциты (%) → lymphocytes
- Лимфоциты (абс.) → lymphocytes_abs
- Моноциты (%) → monocytes
- Моноциты (абс.) → monocytes_abs
- Эозинофилы (%) → eosinophils
- Эозинофилы (абс.) → eosinophils_abs
- Базофилы (%) → basophils
- Базофилы (абс.) → basophils_abs
- СОЭ → esr
- Тромбокрит → thrombocrit
- Средний объем тромбоцита / MPV → mpv

For values not found in the document, use null.
Parse numeric values carefully - commas are decimal separators (6,13 = 6.13).

Return ONLY the JSON object, no additional text."""

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        
        answer_str = response.choices[0].message.content.strip()
        logger.info(f"OpenAI raw response: {answer_str[:500]}...")  # Log first 500 chars
        answer = json.loads(answer_str)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse LLM response")
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM processing error: {str(e)}")

    # Step 3: Build response with proper typing
    # OpenAI now returns English keys directly, so we just need to validate and structure
    response_data: Dict[str, Any] = {}
    
    # Get all possible English keys from the mapping
    all_english_keys = set(nazvaniya_mapping.values())
    
    for english_key in all_english_keys:
        value = answer.get(english_key)
        
        if value is not None and isinstance(value, dict):
            # Extract numeric value, handling potential string numbers
            raw_value = value.get("value")
            numeric_value = None
            if raw_value is not None:
                try:
                    numeric_value = float(raw_value) if raw_value != "" else None
                except (ValueError, TypeError):
                    numeric_value = None
            
            response_data[english_key] = AnalyteResult(
                value=numeric_value,
                ref=value.get("ref", "")
            )
        else:
            response_data[english_key] = None
    
    # Add patient info
    response_data["full_name"] = answer.get("full_name", "")
    
    # Handle age - could be int or need calculation from birth date
    age_value = answer.get("age")
    if isinstance(age_value, int):
        response_data["age"] = age_value
    elif isinstance(age_value, str) and age_value.isdigit():
        response_data["age"] = int(age_value)
    else:
        response_data["age"] = 0
        
    response_data["sex"] = answer.get("sex", "")
    response_data["date"] = answer.get("date", "")
    
    logger.info(f"Successfully parsed blood test for: {response_data.get('full_name')}")
    logger.info(f"Response data: {response_data}")
    
    return ParsedBloodTestResponse(**response_data)

@router.post("/parse-blood-test", response_model=BloodTestResults)
async def parse_blood_test(file: UploadFile = File(...)):
    """
    Парсит файл с результатами анализа крови
    
    Args:
        file: Загруженный файл (PDF, JPG, JPEG, PNG)
        
    Returns:
        BloodTestResults: Извлеченные данные анализа крови
    """
    try:
        # Обрабатываем документ
        cbc_data, meta = await document_processor.process_document(file)
        
        # Проверяем наличие данных
        if not document_processor.validate_cbc_data(cbc_data):
            logger.error(f"Failed to extract CBC data from {file.filename}")
            raise HTTPException(status_code=422, detail="CBC not found in document")
        
        # Объединяем данные для создания результата
        combined_data: Dict[str, Union[float, str, None]] = {**cbc_data, **meta}
        result = BloodTestResults(**combined_data)  # type: ignore
        logger.info(f"Successfully processed {file.filename}: {result}")
        
        return result
        
    except MedTechException as e:
        raise handle_medtech_exception(e, 422)
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/blood-results", response_model=SIIResult)
async def calculate_sii(data: BloodTestResults):
    """
    Рассчитывает SII индекс на основе данных анализа крови
    
    Args:
        data: Данные анализа крови
        
    Returns:
        SIIResult: Результат расчета
    """
    try:
        logger.info(f"Calculating SII for data: {data}")
        
        # Рассчитываем SII
        result = sii_calculator.calculate_sii(data)
        
        logger.info(f"SII calculation successful: {result}")
        return result
        
    except MedTechException as e:
        raise handle_medtech_exception(e, 400)
    except Exception as e:
        logger.error(f"Unexpected error calculating SII: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/parse-pdf-llamaindex", response_model=ParsedDocument)
async def parse_pdf_with_llamaindex(file: UploadFile = File(...)):
    """
    Парсит PDF документ с помощью LlamaIndex (без сохранения в БД)
    
    Args:
        file: Загруженный PDF файл
        
    Returns:
        ParsedDocument: Извлеченный текст и метаданные документа
    """
    try:
        llamaindex_service = get_llamaindex_service()
        result = await llamaindex_service.parse_pdf_document(file)
        
        logger.info(f"Успешно обработан PDF файл с LlamaIndex: {file.filename}")
        return ParsedDocument(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке PDF с LlamaIndex {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.post("/parse-blood-test-pdf", response_model=ProcessedBloodTestDocument)
async def parse_blood_test_pdf_with_database(
    file: UploadFile = File(...),
    user_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Парсит PDF с анализом крови и сохраняет данные в Supabase базу данных
    
    Args:
        file: Загруженный PDF файл с анализом крови
        user_id: ID пользователя (опционально)
        db: Сессия базы данных
        
    Returns:
        ProcessedBloodTestDocument: Результат обработки с информацией о сохранении
    """
    start_time = time.time()
    
    try:
        # Инициализируем сервисы
        llamaindex_service = get_llamaindex_service()
        db_service = await get_database_service(db)
        
        # Создаем сессию анализа
        file_size = len(await file.read())
        await file.seek(0)  # Возвращаем указатель в начало файла
        
        analysis_session = await db_service.create_analysis_session(
            filename=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            user_id=user_id
        )
        
        # Парсим PDF документ
        parse_result = await llamaindex_service.parse_pdf_document(file)
        extracted_text = parse_result.get("content", "")
        
        # Обновляем сессию с извлеченным текстом
        await db_service.update_analysis_session(
            session_id=analysis_session.session_id,
            status="processing",
            extracted_text=extracted_text
        )
        
        # Пытаемся извлечь данные анализа крови из текста
        blood_test_data = None
        blood_test_record_id = None
        
        try:
            # Здесь должна быть логика извлечения структурированных данных
            # из текста PDF с помощью LLM или других методов
            # Пока используем пример данных для демонстрации
            
            blood_test_data = await _extract_blood_test_data_from_text(extracted_text)
            
            if blood_test_data:
                # Сохраняем данные анализа крови
                blood_test_record = await db_service.save_blood_test_results(
                    blood_test_data=blood_test_data,
                    session_id=analysis_session.session_id,
                    source_filename=file.filename,
                    user_id=user_id
                )
                blood_test_record_id = blood_test_record.id
                
                # Обновляем сессию со статусом завершения
                await db_service.update_analysis_session(
                    session_id=analysis_session.session_id,
                    status="completed",
                    blood_test_id=blood_test_record_id
                )
                
                logger.info(f"✅ Успешно сохранены данные анализа крови: {blood_test_record_id}")
            else:
                # Обновляем сессию, если данные не удалось извлечь
                await db_service.update_analysis_session(
                    session_id=analysis_session.session_id,
                    status="completed",
                    error_message="Не удалось извлечь структурированные данные анализа крови"
                )
                
        except Exception as extraction_error:
            logger.warning(f"Ошибка при извлечении данных анализа крови: {extraction_error}")
            await db_service.update_analysis_session(
                session_id=analysis_session.session_id,
                status="completed",
                error_message=f"Ошибка извлечения данных: {str(extraction_error)}"
            )
        
        processing_time = time.time() - start_time
        
        # Формируем ответ
        response = ProcessedBloodTestDocument(
            filename=file.filename,
            content=extracted_text,
            session_id=analysis_session.session_id,
            blood_test_record_id=blood_test_record_id,
            processing_status="completed",
            blood_test_data=blood_test_data.dict() if blood_test_data else None,
            file_size=file_size,
            processing_time=processing_time
        )
        
        logger.info(f"🏥 Успешно обработан документ анализа крови: {file.filename} (Сессия: {analysis_session.session_id})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при обработке PDF {file.filename}: {str(e)}")
        
        # Пытаемся обновить сессию с ошибкой
        try:
            if 'analysis_session' in locals():
                await db_service.update_analysis_session(
                    session_id=analysis_session.session_id,
                    status="failed",
                    error_message=str(e)
                )
        except:
            pass
            
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


async def _extract_blood_test_data_from_text(text: str) -> BloodTestResultsSchema:
    """
    Извлекает структурированные данные анализа крови из текста
    
    Args:
        text: Извлеченный текст из PDF
        
    Returns:
        BloodTestResultsSchema: Структурированные данные или None
        
    TODO: Реализовать с помощью LLM для автоматического извлечения данных
    """
    try:
        # Здесь должна быть логика с использованием LLM для извлечения данных
        # Пока возвращаем None, если не удается найти ключевые слова
        
        # Простая проверка на наличие ключевых слов анализа крови
        blood_keywords = [
            "гемоглобин", "эритроциты", "лейкоциты", "тромбоциты",
            "нейтрофилы", "лимфоциты", "моноциты", "эозинофилы", "базофилы"
        ]
        
        text_lower = text.lower()
        found_keywords = [keyword for keyword in blood_keywords if keyword in text_lower]
        
        if len(found_keywords) < 3:  # Минимум 3 ключевых слова для распознавания как анализ крови
            logger.warning("Недостаточно ключевых слов для распознавания анализа крови")
            return None
        
        # Для демонстрации возвращаем примерные данные
        # В реальной реализации здесь должен быть вызов LLM
        from app.schemas.user_uploads import PatientInfo, TestMetadata, AnalyteResult
        from datetime import datetime
        
        # Примерные данные для демонстрации
        demo_data = BloodTestResultsSchema(
            patient=PatientInfo(
                full_name="Извлечено из PDF",
                gender="Не определено",
                age=0,
                patient_id=None
            ),
            metadata=TestMetadata(
                sample_taken_date=datetime.now(),
                result_printed_date=datetime.now(),
                laboratory="Извлечено из PDF"
            ),
            analytes={
                "Обработка": AnalyteResult(value=1.0, unit="статус", reference_range="демо")
            }
        )
        
        logger.info(f"🧪 Найдены ключевые слова анализа крови: {found_keywords}")
        return demo_data
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных анализа крови: {e}")
        return None


@router.post("/parse-blood-test-pdf-normalized", response_model=ProcessedBloodTestDocument)
async def parse_blood_test_pdf_with_normalized_database(
    file: UploadFile = File(...),
    user_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Парсит PDF с анализом крови и сохраняет данные в нормализованные таблицы Supabase
    
    Args:
        file: Загруженный PDF файл с анализом крови
        user_id: ID пользователя (опционально)
        db: Сессия базы данных
        
    Returns:
        ProcessedBloodTestDocument: Результат обработки с информацией о сохранении
    """
    start_time = time.time()
    
    try:
        # Инициализируем сервисы
        llamaindex_service = get_llamaindex_service()
        db_service = await get_normalized_database_service(db)
        
        # Создаем сессию анализа
        file_size = len(await file.read())
        await file.seek(0)  # Возвращаем указатель в начало файла
        
        analysis_session = await db_service.create_analysis_session(
            filename=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            user_id=user_id
        )
        
        # Парсим PDF документ
        parse_result = await llamaindex_service.parse_pdf_document(file)
        extracted_text = parse_result.get("content", "")
        
        # Обновляем сессию с извлеченным текстом
        await db_service.update_analysis_session(
            session_id=analysis_session.session_id,
            status="processing",
            extracted_text=extracted_text
        )
        
        # Пытаемся извлечь данные анализа крови из текста
        blood_test_data = None
        blood_test_record_id = None
        
        try:
            # Извлекаем структурированные данные
            blood_test_data = await _extract_blood_test_data_from_text(extracted_text)
            
            if blood_test_data:
                # Сохраняем данные в нормализованные таблицы
                blood_test_result = await db_service.save_blood_test_results(
                    blood_test_data=blood_test_data,
                    session_id=analysis_session.session_id,
                    source_filename=file.filename,
                    user_id=user_id
                )
                blood_test_record_id = blood_test_result.id
                
                # Обновляем сессию со статусом завершения
                await db_service.update_analysis_session(
                    session_id=analysis_session.session_id,
                    status="completed",
                    blood_test_id=blood_test_record_id
                )
                
                logger.info(f"✅ Успешно сохранены данные в нормализованные таблицы: {blood_test_record_id}")
            else:
                # Обновляем сессию, если данные не удалось извлечь
                await db_service.update_analysis_session(
                    session_id=analysis_session.session_id,
                    status="completed",
                    error_message="Не удалось извлечь структурированные данные анализа крови"
                )
                
        except Exception as extraction_error:
            logger.warning(f"Ошибка при извлечении данных анализа крови: {extraction_error}")
            await db_service.update_analysis_session(
                session_id=analysis_session.session_id,
                status="completed",
                error_message=f"Ошибка извлечения данных: {str(extraction_error)}"
            )
        
        processing_time = time.time() - start_time
        
        # Формируем ответ
        response = ProcessedBloodTestDocument(
            filename=file.filename,
            content=extracted_text,
            session_id=analysis_session.session_id,
            blood_test_record_id=blood_test_record_id,
            processing_status="completed",
            blood_test_data=blood_test_data.dict() if blood_test_data else None,
            file_size=file_size,
            processing_time=processing_time
        )
        
        logger.info(f"🏥 Успешно обработан документ анализа крови в нормализованные таблицы: {file.filename}")
        logger.info(f"📊 Сессия: {analysis_session.session_id}, Результат: {blood_test_record_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при обработке PDF {file.filename}: {str(e)}")
        
        # Пытаемся обновить сессию с ошибкой
        try:
            if 'analysis_session' in locals():
                await db_service.update_analysis_session(
                    session_id=analysis_session.session_id,
                    status="failed",
                    error_message=str(e)
                )
        except:
            pass
            
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.post("/query-document", response_model=DocumentQueryResponse)
async def query_document_with_llamaindex(query_data: DocumentQuery):
    """
    Выполняет запрос к документу с помощью LlamaIndex
    
    Args:
        query_data: Запрос и документы для поиска
        
    Returns:
        DocumentQueryResponse: Ответ на запрос с контекстом
    """
    try:
        llamaindex_service = get_llamaindex_service()
        result = await llamaindex_service.query_document(
            query_data.documents, 
            query_data.query
        )
        
        logger.info(f"Выполнен запрос к документу: {query_data.query[:50]}...")
        return DocumentQueryResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при выполнении запроса: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.get("/health")
def health_check():
    """Проверка состояния API"""
    return {
        "status": "healthy",
        "services": {
            "document_processor": "operational",
            "sii_calculator": "operational",
            "llamaindex_service": "operational"
        }
    } 