"""
API эндпоинты для MedTech приложения
"""
import ast
import os
from typing import Dict, Any, Union
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import time

from app.core.exceptions import handle_medtech_exception, MedTechException
from app.schemas.blood_results import BloodTestResults, SIIResult
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
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
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


@router.post("/v3/blood-tests/upload-multiple-files")
async def parse_blood_test_v2_(
    files: List[UploadFile] = File(...)
):
    return {'hemoglobin': {'value': 165.0, 'ref': '132 - 173'}, 'erythrocytes': {'value': 5.3, 'ref': '4.30 - 5.70'}, 'mcv': {'value': 91.1, 'ref': '80.0 - 99.0'}, 'rdw': {'value': 11.8, 'ref': '11.6 - 14.8'}, 'mch': {'value': 31.1, 'ref': '27.0 - 34.0'}, 'mchc': {'value': 34.2, 'ref': '32.0 - 37.0'}, 'hematocrit': {'value': 48.3, 'ref': '39.0 - 49.0'}, 'platelets': {'value': 326.0, 'ref': '150 - 400'}, 'wbc': {'value': 5.98, 'ref': '4.50 - 11.00'}, 'esr': {'value': 9.0, 'ref': '< 15'}, 'neutrophils': {'value': 40.2, 'ref': '48.0 - 78.0'}, 'band_neutrophils': None, 'segmented_neutrophils': None, 'lymphocytes': {'value': 48.5, 'ref': '19.0 - 37.0'}, 'monocytes': {'value': 8.0, 'ref': '3.0 - 11.0'}, 'eosinophils': {'value': 3.0, 'ref': '1.0 - 5.0'}, 'basophils': {'value': 0.3, 'ref': '< 1.0'}, 'neutrophils_abs': {'value': 2.4, 'ref': '1.78 - 5.38'}, 'lymphocytes_abs': {'value': 2.9, 'ref': '1.32 - 3.57'}, 'monocytes_abs': {'value': 0.48, 'ref': '0.20 - 0.95'}, 'eosinophils_abs': {'value': 0.18, 'ref': '0.00 - 0.70'}, 'basophils_abs': {'value': 0.02, 'ref': '0.00 - 0.20'}, 'glucose': None, 'protein_total': None, 'albumin': None, 'urea': None, 'creatinine': None, 'uric_acid': None, 'bilirubin_total': None, 'bilirubin_direct': None, 'bilirubin_indirect': None, 'alt': None, 'ast': None, 'alkaline_phosphatase': None, 'ggt': None, 'ldh': None, 'cholesterol': None, 'hdl_cholesterol': None, 'ldl_cholesterol': None, 'triglycerides': None, 'calcium_total': None, 'potassium': None, 'sodium': None, 'chlorides': None, 'phosphorus': None, 'magnesium': None, 'prothrombin_time': None, 'prothrombin_quick': None, 'inr': None, 'aptt': None, 'fibrinogen': None, 'thrombin_time': None, 'antithrombin_iii': None, 'd_dimer': None, 'crp': None, 'rheumatoid_factor': None, 'b_hcg_total': None, 'tsh': None, 't3': None, 't4': None, 'prolactin': None, 'lh': None, 'fsh': None, 'estradiol': None, 'testosterone': None, 'cortisol': None, 'reticulocytes': None, 'thrombocrit': None, 'mpv': None, 'folic_acid': None, 'vitamin_d': None, 'vitamin_a': None, 'vitamin_b1': None, 'vitamin_b2': None, 'vitamin_b3': None, 'vitamin_b5': None, 'vitamin_b6': None, 'vitamin_b7': None, 'vitamin_b9': None, 'vitamin_b12': None, 'vitamin_c': None, 'vitamin_e': None, 'vitamin_k': None, 'full_name': 'ДЖУНУСОВ ДИНМУХАМЕД САИНҰЛЫ', 'age': 31, 'sex': 'Мужской', 'date': '01.06.2024'}
    #
    # return {'hemoglobin': {'value': 114.0, 'ref': '117 - 160'}, 'erythrocytes': {'value': 4.32, 'ref': '3.8 - 5.3'}, 'mcv': {'value': 78.2, 'ref': '80 - 100'}, 'rdw': None, 'mch': {'value': 26.4, 'ref': '26.5 - 33.5'}, 'mchc': {'value': 33.7, 'ref': '31 - 38'}, 'hematocrit': {'value': 33.8, 'ref': '> 35'}, 'platelets': {'value': 205.0, 'ref': '150 - 400'}, 'wbc': {'value': 4.6, 'ref': '4.5 - 11'}, 'esr': {'value': 36.0, 'ref': '< 23'}, 'neutrophils': {'value': 74.0, 'ref': '47 - 72'}, 'band_neutrophils': None, 'segmented_neutrophils': None, 'lymphocytes': {'value': 14.0, 'ref': '19 - 37'}, 'monocytes': {'value': 9.0, 'ref': '2 - 9'}, 'eosinophils': {'value': 2.0, 'ref': '< 5'}, 'basophils': {'value': 0.0, 'ref': '< 1.2'}, 'neutrophils_abs': {'value': 3.38, 'ref': '1.5 - 7'}, 'lymphocytes_abs': {'value': 0.66, 'ref': '1 - 4.8'}, 'monocytes_abs': {'value': 0.42, 'ref': '< 0.7'}, 'eosinophils_abs': {'value': 0.1, 'ref': '< 0.45'}, 'basophils_abs': {'value': 0.01, 'ref': '< 0.1'}, 'glucose': None, 'protein_total': None, 'albumin': None, 'urea': None, 'creatinine': None, 'uric_acid': None, 'bilirubin_total': None, 'bilirubin_direct': None, 'bilirubin_indirect': None, 'alt': None, 'ast': None, 'alkaline_phosphatase': None, 'ggt': None, 'ldh': None, 'cholesterol': None, 'hdl_cholesterol': None, 'ldl_cholesterol': None, 'triglycerides': None, 'calcium_total': None, 'potassium': None, 'sodium': None, 'chlorides': None, 'phosphorus': None, 'magnesium': None, 'prothrombin_time': None, 'prothrombin_quick': None, 'inr': None, 'aptt': None, 'fibrinogen': None, 'thrombin_time': None, 'antithrombin_iii': None, 'd_dimer': None, 'crp': None, 'rheumatoid_factor': None, 'b_hcg_total': None, 'tsh': None, 't3': None, 't4': None, 'prolactin': None, 'lh': None, 'fsh': None, 'estradiol': None, 'testosterone': None, 'cortisol': None, 'reticulocytes': None, 'thrombocrit': None, 'mpv': None, 'folic_acid': None, 'vitamin_d': None, 'vitamin_a': None, 'vitamin_b1': None, 'vitamin_b2': None, 'vitamin_b3': None, 'vitamin_b5': None, 'vitamin_b6': None, 'vitamin_b7': None, 'vitamin_b9': None, 'vitamin_b12': None, 'vitamin_c': None, 'vitamin_e': None, 'vitamin_k': None, 'full_name': 'ТУРГАНБАЕВА САГЫНГАН РЫСКУЛОВНА', 'age': 63, 'sex': 'Женский', 'date': '29.05.2025'}

    if not os.getenv("LLAMA_CLOUD_API_KEY"):
        raise HTTPException(status_code=500, detail="LLAMA_CLOUD_API_KEY is not set")

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    contents = ""
    for file in files:
        print(file.filename)
        file_content = file.file.read()
        parser = LlamaParse(result_type="markdown", language='ru')
        documents = await parser.aparse(file_content, extra_info={"file_name": file.filename})

        contents += documents.get_markdown_documents()[0].text
    # Записываем содержимое в файл для отладки
    with open("parsed_blood_test_contents.txt", "w", encoding="utf-8") as f:
        f.write(contents)

    system_prompt = """You are a medical data parser. Extract full_name, age ("Жасы (Возраст):"), sex(Пол), date (Дата сдачи анализа) and also all analyte names ("названия анализов" or "Компонент"), their results ("результат" or "Нәтиже"), units ("единицы измерения"), and reference values ("Референс мағыналары(Референсные значения)") from the clinical blood test table(s) in the text.
        Return a JSON dictionary mapping the Russian analyte name to a dictionary of 'value' (as float or str), 'units' (as str), and, where available, 'ref' (reference range as str).
        If there is no analyte table or no blood test result, return an empty dictionary."""

    user_prompt = f"""
    В данном тексте в формате markdown содержатся таблицы с результатами лабораторных анализов на русском и казахском языках.
    Найди для каждого анализа из этого списка: {nazvaniya_analizov} -- значение "Результат" из текста (всегда числовое!),
    если такого анализа нет в тексте, верни None для этого ключа. Верни только Python словарь, ключи — из этого списка, значения — найденное значение (или None) и Референсные значения. Также full_name, age (всегда числовое!), sex(Пол: Мужской или Женский), and date (Дата сдачи анализа).
    Текст: '''{contents}'''
    """


    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    response = client.chat.completions.create(
        model="gpt-4.1",  # или "gpt-3.5-turbo", если нет доступа к gpt-4
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    # print(type(response.choices[0].message.content))
    answer_str = response.choices[0].message.content.strip()
    answer = ast.literal_eval(answer_str)

    final = {}
    for value in nazvaniya_analizov:
        final[nazvaniya_mapping[value]] = answer.get(value, None)
    final["full_name"] = answer['full_name']
    final["age"] = answer['age']
    final["sex"] = answer['sex']
    final["date"] = answer['date']
    print(final)

    return final

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