from fastapi import HTTPException
from typing import Optional


class MedTechException(Exception):
    """Базовое исключение для MedTech приложения"""
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class DocumentProcessingError(MedTechException):
    """Исключение для ошибок обработки документов"""
    pass


class BloodTestExtractionError(MedTechException):
    """Исключение для ошибок извлечения данных анализа крови"""
    pass


class UnsupportedFileFormatError(MedTechException):
    """Исключение для неподдерживаемых форматов файлов"""
    pass


class SIICalculationError(MedTechException):
    """Исключение для ошибок расчета SII"""
    pass


def handle_medtech_exception(exc: MedTechException, status_code: int = 400) -> HTTPException:
    """Конвертирует MedTech исключения в HTTP исключения"""
    return HTTPException(
        status_code=status_code,
        detail={
            "message": exc.message,
            "code": exc.code,
            "type": exc.__class__.__name__
        }
    ) 