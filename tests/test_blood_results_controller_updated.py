"""
Обновленные тесты для blood results контроллера с новой архитектурой
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.schemas.blood_results import SIILevel
from src.services.helper import interpret_sii


class TestBloodResultsControllerRefactored:
    """Тесты для обновленного контроллера анализа крови"""

    def test_successful_sii_calculation(self, client):
        """Тест успешного расчета SII"""
        test_data = {
            "neutrophils_absolute": 4.0,
            "platelets": 250.0,
            "lymphocytes_absolute": 2.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["sii"] == 500.0  # (4.0 * 250.0) / 2.0
        assert "level" in result
        assert "interpretation" in result

    def test_missing_required_neutrophils_absolute(self, client):
        """Тест ошибки при отсутствии neutrophils_absolute"""
        test_data = {
            "platelets": 250.0,
            "lymphocytes_absolute": 2.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        assert response.status_code == 400
        response_data = response.json()
        assert "Missing required fields for SII calculation: neutrophils_absolute" in response_data["detail"]["message"]

    def test_missing_required_platelets(self, client):
        """Тест ошибки при отсутствии platelets"""
        test_data = {
            "neutrophils_absolute": 4.0,
            "lymphocytes_absolute": 2.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        assert response.status_code == 400
        response_data = response.json()
        assert "Missing required fields for SII calculation: platelets" in response_data["detail"]["message"]

    def test_missing_required_lymphocytes_absolute(self, client):
        """Тест ошибки при отсутствии lymphocytes_absolute"""
        test_data = {
            "neutrophils_absolute": 4.0,
            "platelets": 250.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        assert response.status_code == 400
        response_data = response.json()
        assert "Missing required fields for SII calculation: lymphocytes_absolute" in response_data["detail"]["message"]

    def test_zero_lymphocytes_absolute(self, client):
        """Тест ошибки при нулевом значении lymphocytes_absolute"""
        test_data = {
            "neutrophils_absolute": 4.0,
            "platelets": 250.0,
            "lymphocytes_absolute": 0.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        assert response.status_code == 400
        response_data = response.json()
        assert "Lymphocytes absolute count cannot be zero" in response_data["detail"]["message"]

    def test_without_cancer_type(self, client):
        """Тест расчета SII без указания типа рака"""
        test_data = {
            "neutrophils_absolute": 3.0,
            "platelets": 200.0,
            "lymphocytes_absolute": 1.5
        }
        
        response = client.post("/blood-results", json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["sii"] == 400.0  # (3.0 * 200.0) / 1.5

    def test_high_sii_calculation(self, client):
        """Тест расчета высокого SII"""
        test_data = {
            "neutrophils_absolute": 8.0,
            "platelets": 500.0,
            "lymphocytes_absolute": 1.0,
            "cancer_type": "C25"
        }
        
        response = client.post("/blood-results", json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["sii"] == 4000.0  # (8.0 * 500.0) / 1.0

    def test_low_sii_calculation(self, client):
        """Тест расчета низкого SII"""
        test_data = {
            "neutrophils_absolute": 2.0,
            "platelets": 100.0,
            "lymphocytes_absolute": 4.0,
            "cancer_type": "C50"
        }
        
        response = client.post("/blood-results", json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["sii"] == 50.0  # (2.0 * 100.0) / 4.0

    def test_decimal_precision(self, client):
        """Тест точности округления SII"""
        test_data = {
            "neutrophils_absolute": 3.33,
            "platelets": 333.33,
            "lymphocytes_absolute": 1.11,
            "cancer_type": "C16"
        }
        
        response = client.post("/blood-results", json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        # (3.33 * 333.33) / 1.11 ≈ 999.99
        assert result["sii"] == 999.99

    def test_complete_blood_test_data(self, client):
        """Тест с полными данными анализа крови"""
        test_data = {
            "hemoglobin": 14.5,
            "white_blood_cells": 6.8,
            "red_blood_cells": 4.5,
            "platelets": 250.0,
            "neutrophils_percent": 60.0,
            "neutrophils_absolute": 4.1,
            "lymphocytes_percent": 30.0,
            "lymphocytes_absolute": 2.0,
            "monocytes_percent": 5.0,
            "monocytes_absolute": 0.3,
            "eosinophils_percent": 3.0,
            "eosinophils_absolute": 0.2,
            "basophils_percent": 2.0,
            "basophils_absolute": 0.1,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["sii"] == 512.5  # (4.1 * 250.0) / 2.0


class TestNewEndpoints:
    """Тесты для новых эндпоинтов"""
    
    def test_health_check(self, client):
        """Тест проверки состояния API"""
        response = client.get("/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "healthy"
        assert "services" in result
        assert "document_processor" in result["services"]
        assert "sii_calculator" in result["services"]
    
    def test_root_endpoint(self, client):
        """Тест корневого эндпоинта"""
        response = client.get("/")
        
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == "MedTech API"
        assert result["version"] == "2.0"


class TestSIICalculatorService:
    """Тесты для SII калькулятора"""
    
    def test_sii_calculator_import(self):
        """Тест импорта SII калькулятора"""
        from src.services.sii_calculator import SIICalculator
        
        calculator = SIICalculator()
        assert calculator is not None

    def test_sii_calculator_validation(self):
        """Тест валидации SII калькулятора"""
        from src.services.sii_calculator import SIICalculator
        from src.schemas.blood_results import BloodTestResults
        from src.core.exceptions import SIICalculationError
        
        calculator = SIICalculator()
        
        # Тест с неполными данными
        data = BloodTestResults(neutrophils_absolute=None, platelets=250.0, lymphocytes_absolute=2.0)
        
        with pytest.raises(SIICalculationError) as exc_info:
            calculator.calculate_sii(data)
        
        assert "Missing required fields" in str(exc_info.value)


class TestLabParsers:
    """Тесты для парсеров лабораторий"""
    
    def test_lab_parser_factory_import(self):
        """Тест импорта фабрики парсеров"""
        from src.services.lab_parsers import LabParserFactory
        
        factory = LabParserFactory()
        assert factory is not None

    def test_invitro_parser_detection(self):
        """Тест обнаружения лаборатории Инвитро"""
        from src.services.lab_parsers import InvitroParser
        
        parser = InvitroParser()
        pages = ["некий текст с инвитро лабораторией"]
        
        assert parser.detect_lab_type(pages) == True

    def test_olymp_parser_detection(self):
        """Тест обнаружения лаборатории Олимп"""
        from src.services.lab_parsers import OlympParser
        
        parser = OlympParser()
        pages = ["некий текст с олимп лабораторией"]
        
        assert parser.detect_lab_type(pages) == True


class TestDocumentProcessor:
    """Тесты для процессора документов"""
    
    def test_document_processor_import(self):
        """Тест импорта процессора документов"""
        from src.services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        assert processor is not None

    def test_cbc_data_validation(self):
        """Тест валидации данных CBC"""
        from src.services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # Тест с валидными данными
        valid_data = {"hemoglobin": 14.5, "neutrophils_absolute": 4.0}
        assert processor.validate_cbc_data(valid_data) == True
        
        # Тест с пустыми данными
        empty_data = {}
        assert processor.validate_cbc_data(empty_data) == False


@pytest.mark.parametrize("cancer_code,expected_present", [
    ("C34", True),  # Рак легкого
    ("C25", True),  # Рак поджелудочной железы
    ("C16", True),  # Рак желудка
    ("UNKNOWN", False),  # Неизвестный тип
])
def test_cancer_types_support(cancer_code, expected_present):
    """Тест поддержки различных типов рака"""
    from src.schemas.blood_results import cancer_types
    
    codes = []
    for cancer_type in cancer_types:
        codes.extend(cancer_type.icd10_codes)
    
    if expected_present:
        assert cancer_code in codes
    else:
        assert cancer_code not in codes 