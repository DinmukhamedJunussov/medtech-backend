"""
API эндпоинты для MedTech приложения
"""
from typing import Dict, Any, Union
from fastapi import APIRouter, File, HTTPException, UploadFile
from loguru import logger

from src.core.exceptions import handle_medtech_exception, MedTechException
from src.schemas.blood_results import BloodTestResults, SIIResult
from src.services.document_processor import DocumentProcessor
from src.services.sii_calculator import SIICalculator

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
        "description": "API для анализа результатов анализа крови и расчета SII индекса"
    }


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
        SIIResult: Результат расчета SII индекса
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


@router.get("/health")
def health_check():
    """Проверка состояния API"""
    return {
        "status": "healthy",
        "services": {
            "document_processor": "operational",
            "sii_calculator": "operational"
        }
    } 