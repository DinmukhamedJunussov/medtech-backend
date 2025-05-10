# Экспортируем функции OCR сервиса
from .ocr_aws import (
    analyze_document,
    extract_full_text,
    extract_tables,
    process_blood_test_data,
    extract_patient_meta
)

# Другие экспорты... 