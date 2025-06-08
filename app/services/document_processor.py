"""
Сервис для обработки документов
"""
import io
from typing import Dict, List, Any, Tuple, Optional
from fastapi import UploadFile
from loguru import logger

import fitz  # type: ignore  # PyMuPDF
import pdfplumber

from app.core.exceptions import UnsupportedFileFormatError, DocumentProcessingError
from app.services.lab_parsers import LabParserFactory
from app.services.ocr_aws import analyze_document, extract_full_text, extract_tables, process_blood_test_data, extract_patient_meta


class DocumentProcessor:
    """Основной процессор документов"""
    
    def __init__(self):
        self.lab_parser_factory = LabParserFactory()
    
    async def process_document(self, file: UploadFile) -> Tuple[Dict[str, float], Dict[str, str]]:
        """
        Обрабатывает загруженный документ и извлекает данные анализа крови
        
        Args:
            file: Загруженный файл
            
        Returns:
            Tuple[Dict[str, float], Dict[str, str]]: Данные CBC и метаданные
        """
        if file.filename is None:
            raise DocumentProcessingError("Filename is required")
        
        filename = file.filename.lower()
        file_bytes = await file.read()
        
        try:
            if filename.endswith(".pdf"):
                return await self._process_pdf(file_bytes)
            elif filename.endswith((".jpg", ".jpeg", ".png")):
                return await self._process_image(file_bytes)
            else:
                raise UnsupportedFileFormatError("Only PDF, JPG, JPEG and PNG files are supported")
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            if isinstance(e, (DocumentProcessingError, UnsupportedFileFormatError)):
                raise
            raise DocumentProcessingError(f"Document processing failed: {str(e)}")
    
    async def _process_pdf(self, file_bytes: bytes) -> Tuple[Dict[str, float], Dict[str, str]]:
        """Обрабатывает PDF файлы"""
        pages = self._extract_text_from_pdf(file_bytes)
        if not pages:
            raise DocumentProcessingError("Text extraction failed")
        
        # Извлекаем метаданные
        meta = self._extract_meta_from_pages(pages)
        
        # Извлекаем данные CBC
        cbc_data = self.lab_parser_factory.extract_values(pages)
        
        return cbc_data, meta
    
    async def _process_image(self, file_bytes: bytes) -> Tuple[Dict[str, float], Dict[str, str]]:
        """Обрабатывает изображения с помощью AWS Textract"""
        try:
            # Получаем ответ от Textract
            raw_response = await analyze_document(file_bytes, return_raw_response=True)
            
            if not isinstance(raw_response, dict):
                logger.error(f"Unexpected response type from Textract: {type(raw_response)}")
                raise DocumentProcessingError("OCR service returned invalid data")
            
            # Извлекаем текст
            text_content = extract_full_text(raw_response)
            pages = [text_content] if text_content else []
            
            if not text_content:
                raise DocumentProcessingError("Text extraction failed")
            
            logger.info(f"Extracted text from image using Amazon Textract: {text_content[:500]}...")
            
            # Извлечение метаданных пациента
            meta = extract_patient_meta(raw_response)
            logger.info(f"Extracted patient metadata from image: {meta}")
            
            # Извлекаем данные CBC стандартным методом
            cbc_data = self.lab_parser_factory.extract_values(pages)
            
            # Если данные не найдены, пробуем через таблицы Textract
            if not any(cbc_data.values()):
                tables_data = extract_tables(raw_response)
                logger.info(f"Extracted {len(tables_data)} tables from image")
                
                additional_blood_data = process_blood_test_data(tables_data, text_content)
                if additional_blood_data:
                    cbc_data.update(additional_blood_data)
                    logger.info(f"Found additional blood test data using Textract: {additional_blood_data}")
            
            return cbc_data, meta
            
        except Exception as e:
            logger.error(f"Error during image analysis: {str(e)}")
            raise DocumentProcessingError(f"Image analysis failed: {str(e)}")
    
    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> List[str]:
        """Извлекает текст из PDF файла"""
        pages = []
        
        # Сначала пробуем pdfplumber
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt and txt.strip():
                        pages.append(txt)
        except Exception:
            logger.warning("pdfplumber extraction failed, trying PyMuPDF")
        
        # Если не получилось, пробуем PyMuPDF
        if not pages:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for page in doc:
                    txt = page.get_text()  # type: ignore
                    if txt and txt.strip():
                        pages.append(txt)
            except Exception:
                logger.error("Both PDF extraction methods failed")
        
        return pages
    
    def _extract_meta_from_pages(self, pages: List[str]) -> Dict[str, str]:
        """Извлекает метаданные из страниц PDF"""
        import re
        
        meta: Dict[str, str] = {}
        
        for page in pages:
            # Извлекаем диагноз если найден
            cancer_pattern = re.search(r"диагноз[:\s]+([A-Z]\d+)", page, re.IGNORECASE)
            if cancer_pattern and not meta.get('cancer_type'):
                meta['cancer_type'] = cancer_pattern.group(1)
        
        return meta
    
    def validate_cbc_data(self, cbc_data: Dict[str, float]) -> bool:
        """Проверяет наличие минимально необходимых данных CBC"""
        required_fields = [
            "hemoglobin", "white_blood_cells", "red_blood_cells", "platelets",
            "neutrophils_percent", "neutrophils_absolute",
            "lymphocytes_percent", "lymphocytes_absolute",
            "monocytes_percent", "monocytes_absolute",
            "eosinophils_percent", "eosinophils_absolute",
            "basophils_percent", "basophils_absolute"
        ]
        
        present_fields = [field for field in required_fields if cbc_data.get(field) is not None]
        has_data = len(present_fields) > 0
        
        logger.info(f"CBC validation: {len(present_fields)}/{len(required_fields)} fields present: {present_fields}")
        
        return has_data 