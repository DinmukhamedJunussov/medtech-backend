import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.main import app
from src.schemas.blood_results import BloodTestResults, SIIResult, SIILevel
from src.services.helper import interpret_sii

client = TestClient(app)


class TestBloodResultsController:
    """Тесты для эндпоинта /blood-results"""

    def test_successful_sii_calculation(self):
        """Тест успешного расчета SII"""
        test_data = {
            "neutrophils_absolute": 4.0,
            "platelets": 250.0,
            "lymphocytes_absolute": 2.0,
            "cancer_type": "C34"
        }
        
        with patch('src.main.interpret_sii') as mock_interpret:
            mock_interpret.return_value = (SIILevel.moderate, "Умеренный риск")
            
            response = client.post("/blood-results", json=test_data)
            
            assert response.status_code == 200
            result = response.json()
            assert "sii" in result
            assert "level" in result
            assert "interpretation" in result
            assert result["sii"] == 500.0  # (4.0 * 250.0) / 2.0
            mock_interpret.assert_called_once_with(500.0, "C34")

    def test_missing_required_neutrophils_absolute(self):
        """Тест ошибки при отсутствии neutrophils_absolute"""
        test_data = {
            "platelets": 250.0,
            "lymphocytes_absolute": 2.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        assert response.status_code == 400
        assert "Отсутствуют необходимые значения" in response.json()["detail"]

    def test_missing_required_platelets(self):
        """Тест ошибки при отсутствии platelets"""
        test_data = {
            "neutrophils_absolute": 4.0,
            "lymphocytes_absolute": 2.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        assert response.status_code == 400
        assert "Отсутствуют необходимые значения" in response.json()["detail"]

    def test_missing_required_lymphocytes_absolute(self):
        """Тест ошибки при отсутствии lymphocytes_absolute"""
        test_data = {
            "neutrophils_absolute": 4.0,
            "platelets": 250.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        assert response.status_code == 400
        assert "Отсутствуют необходимые значения" in response.json()["detail"]

    def test_zero_lymphocytes_absolute(self):
        """Тест ошибки при нулевом значении lymphocytes_absolute"""
        test_data = {
            "neutrophils_absolute": 4.0,
            "platelets": 250.0,
            "lymphocytes_absolute": 0.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        assert response.status_code == 400
        assert "не может быть нулевым" in response.json()["detail"]

    def test_without_cancer_type(self):
        """Тест расчета SII без указания типа рака"""
        test_data = {
            "neutrophils_absolute": 3.0,
            "platelets": 200.0,
            "lymphocytes_absolute": 1.5
        }
        
        with patch('src.main.interpret_sii') as mock_interpret:
            mock_interpret.return_value = (SIILevel.low, "Низкий риск")
            
            response = client.post("/blood-results", json=test_data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["sii"] == 400.0  # (3.0 * 200.0) / 1.5
            mock_interpret.assert_called_once_with(400.0, None)

    def test_high_sii_calculation(self):
        """Тест расчета высокого SII"""
        test_data = {
            "neutrophils_absolute": 8.0,
            "platelets": 500.0,
            "lymphocytes_absolute": 1.0,
            "cancer_type": "C25"
        }
        
        with patch('src.main.interpret_sii') as mock_interpret:
            mock_interpret.return_value = (SIILevel.high, "Высокий риск")
            
            response = client.post("/blood-results", json=test_data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["sii"] == 4000.0  # (8.0 * 500.0) / 1.0
            mock_interpret.assert_called_once_with(4000.0, "C25")

    def test_low_sii_calculation(self):
        """Тест расчета низкого SII"""
        test_data = {
            "neutrophils_absolute": 2.0,
            "platelets": 100.0,
            "lymphocytes_absolute": 4.0,
            "cancer_type": "C50"
        }
        
        with patch('src.main.interpret_sii') as mock_interpret:
            mock_interpret.return_value = (SIILevel.very_low, "Очень низкий риск")
            
            response = client.post("/blood-results", json=test_data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["sii"] == 50.0  # (2.0 * 100.0) / 4.0
            mock_interpret.assert_called_once_with(50.0, "C50")

    def test_decimal_precision(self):
        """Тест точности округления SII"""
        test_data = {
            "neutrophils_absolute": 3.33,
            "platelets": 333.33,
            "lymphocytes_absolute": 1.11,
            "cancer_type": "C16"
        }
        
        with patch('src.main.interpret_sii') as mock_interpret:
            mock_interpret.return_value = (SIILevel.moderate, "Умеренный риск")
            
            response = client.post("/blood-results", json=test_data)
            
            assert response.status_code == 200
            result = response.json()
            # (3.33 * 333.33) / 1.11 ≈ 999.99
            assert result["sii"] == 999.99
            mock_interpret.assert_called_once_with(999.99, "C16")

    @patch('src.main.interpret_sii')
    def test_interpret_sii_exception_handling(self, mock_interpret):
        """Тест обработки исключений в interpret_sii"""
        mock_interpret.side_effect = Exception("Тестовая ошибка")
        
        test_data = {
            "neutrophils_absolute": 4.0,
            "platelets": 250.0,
            "lymphocytes_absolute": 2.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        assert response.status_code == 400
        assert "Тестовая ошибка" in response.json()["detail"]

    def test_complete_blood_test_data(self):
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
        
        with patch('src.main.interpret_sii') as mock_interpret:
            mock_interpret.return_value = (SIILevel.moderate, "Умеренный риск")
            
            response = client.post("/blood-results", json=test_data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["sii"] == 512.5  # (4.1 * 250.0) / 2.0


class TestInterpretSiiFunction:
    """Тесты для функции interpret_sii"""

    def test_lung_cancer_very_low_sii(self):
        """Тест очень низкого SII для рака легкого"""
        sii_value = 50.0
        cancer_type = "C34"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Очень низкий уровень воспаления",
                "recommendation": {
                    "title": "Контроль",
                    "items": ["Регулярные анализы", "Здоровый образ жизни"]
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            assert level == SIILevel.very_low
            assert "Очень низкий уровень воспаления" in interpretation
            assert "Контроль:" in interpretation
            mock_get_rec.assert_called_once_with(1)

    def test_lung_cancer_low_sii(self):
        """Тест низкого SII для рака легкого"""
        sii_value = 300.0
        cancer_type = "C34"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Низкий уровень воспаления",
                "recommendation": {
                    "title": "Профилактика",
                    "items": ["Здоровое питание", "Физическая активность"]
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            assert level == SIILevel.low
            assert "Низкий уровень воспаления" in interpretation
            mock_get_rec.assert_called_once_with(2)

    def test_lung_cancer_moderate_sii(self):
        """Тест умеренного SII для рака легкого"""
        sii_value = 800.0
        cancer_type = "C34"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Умеренный уровень воспаления",
                "recommendation": {
                    "title": "Медицинское наблюдение",
                    "items": ["Консультация врача", "Контрольные анализы"]
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            assert level == SIILevel.moderate
            assert "Умеренный уровень воспаления" in interpretation
            mock_get_rec.assert_called_once_with(3)

    def test_lung_cancer_high_sii(self):
        """Тест высокого SII для рака легкого"""
        sii_value = 1200.0
        cancer_type = "C34"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Высокий уровень воспаления",
                "recommendation": {
                    "title": "Срочные меры",
                    "items": ["Срочная консультация онколога", "Дополнительные обследования"]
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            assert level == SIILevel.borderline_high
            assert "Высокий уровень воспаления" in interpretation
            mock_get_rec.assert_called_once_with(4)

    def test_lung_cancer_very_high_sii(self):
        """Тест очень высокого SII для рака легкого"""
        sii_value = 2000.0
        cancer_type = "C34"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Критически высокий уровень воспаления",
                "recommendation": {
                    "title": "Экстренные меры",
                    "items": ["Немедленная госпитализация", "Интенсивное лечение"]
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            assert level == SIILevel.high
            assert "Критически высокий уровень воспаления" in interpretation
            mock_get_rec.assert_called_once_with(5)

    def test_pancreatic_cancer_sii(self):
        """Тест SII для рака поджелудочной железы"""
        sii_value = 500.0
        cancer_type = "C25"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Умеренный риск для поджелудочной железы",
                "recommendation": {
                    "title": "Контроль состояния",
                    "items": ["Повторный анализ через 7-14 дней"]
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            assert level == SIILevel.moderate
            mock_get_rec.assert_called_once_with(3)

    def test_unknown_cancer_type(self):
        """Тест с неизвестным типом рака"""
        sii_value = 500.0
        cancer_type = "UNKNOWN"
        
        level, interpretation = interpret_sii(sii_value, cancer_type)
        
        assert level == SIILevel.low
        assert interpretation == "Нормальный уровень"

    def test_no_cancer_type(self):
        """Тест без указания типа рака"""
        sii_value = 500.0
        cancer_type = None
        
        level, interpretation = interpret_sii(sii_value, cancer_type)
        
        assert level == SIILevel.low
        assert interpretation == "Нормальный уровень"

    def test_boundary_values_lung_cancer(self):
        """Тест граничных значений для рака легкого"""
        cancer_type = "C34"
        
        # Граница между очень низким и низким (100)
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {"summary": "Test", "recommendation": None}
            
            # Ровно 100 - должно попасть в категорию 1 (очень низкий)
            level, _ = interpret_sii(100.0, cancer_type)
            assert level == SIILevel.very_low
            
            # 101 - должно попасть в категорию 2 (низкий)
            level, _ = interpret_sii(101.0, cancer_type)
            assert level == SIILevel.low

    def test_random_recommendation_formatting(self):
        """Тест форматирования случайных рекомендаций"""
        sii_value = 300.0
        cancer_type = "C34"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Тестовое описание",
                "recommendation": {
                    "title": "Тестовая группа",
                    "items": ["Рекомендация 1", "Рекомендация 2", "Рекомендация 3"]
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            # Проверяем что есть описание
            assert "Тестовое описание" in interpretation
            # Проверяем что есть заголовок группы
            assert "Тестовая группа:" in interpretation
            # Проверяем что есть маркеры списка
            assert "•" in interpretation
            # Проверяем что все рекомендации включены
            for item in ["Рекомендация 1", "Рекомендация 2", "Рекомендация 3"]:
                assert item in interpretation

    def test_fallback_when_no_recommendation(self):
        """Тест возврата к fallback, когда нет рекомендаций"""
        sii_value = 300.0
        cancer_type = "C34"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Тестовое описание",
                "recommendation": None
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            assert level == SIILevel.low
            assert interpretation == "Тестовое описание"

    def test_fallback_when_get_random_recommendation_returns_none(self):
        """Тест возврата к fallback, когда get_random_recommendation возвращает None"""
        sii_value = 300.0
        cancer_type = "C34"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = None
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            assert level == SIILevel.low
            assert interpretation == "Описание недоступно"


# Параметризованные тесты для разных типов рака
@pytest.mark.parametrize("cancer_code,cancer_name", [
    ("C34", "Рак легкого"),
    ("C25", "Рак поджелудочной железы"),
    ("C16", "Рак желудка"),
    ("C15", "Рак пищевода"),
    ("C18", "Колоректальный рак"),
    ("C50", "Рак молочной железы"),
    ("C53", "Гинекологические опухоли"),
    ("C22.0", "Гепатоцеллюлярная карцинома"),
])
def test_different_cancer_types(cancer_code, cancer_name):
    """Параметризованный тест для разных типов рака"""
    sii_value = 500.0
    
    with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
        mock_get_rec.return_value = {
            "summary": f"Тест для {cancer_name}",
            "recommendation": {
                "title": "Тестовые рекомендации",
                "items": ["Рекомендация для " + cancer_name]
            }
        }
        
        level, interpretation = interpret_sii(sii_value, cancer_code)
        
        # Проверяем что функция обработала тип рака
        assert level is not None
        assert interpretation is not None
        mock_get_rec.assert_called_once()


@pytest.mark.parametrize("sii_value,expected_level_int", [
    (50, 1),    # Очень низкий
    (300, 2),   # Низкий  
    (800, 3),   # Умеренный
    (1200, 4),  # Высокий
    (2000, 5),  # Очень высокий
])
def test_sii_level_mapping_lung_cancer(sii_value, expected_level_int):
    """Параметризованный тест маппинга SII уровней для рака легкого"""
    cancer_type = "C34"
    
    with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
        mock_get_rec.return_value = {"summary": "Test", "recommendation": None}
        
        level, interpretation = interpret_sii(sii_value, cancer_type)
        
        # Проверяем правильность уровня через from_int
        expected_level = SIILevel.from_int(expected_level_int)
        assert level == expected_level
        mock_get_rec.assert_called_once_with(expected_level_int)


# Интеграционные тесты
class TestBloodResultsIntegration:
    """Интеграционные тесты без моков"""

    def test_end_to_end_calculation(self):
        """Полный end-to-end тест без моков"""
        test_data = {
            "neutrophils_absolute": 4.0,
            "platelets": 250.0,
            "lymphocytes_absolute": 2.0,
            "cancer_type": "C34"
        }
        
        response = client.post("/blood-results", json=test_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["sii"] == 500.0
        assert "level" in result
        assert "interpretation" in result
        # Проверяем что interpretation содержит осмысленный текст
        assert len(result["interpretation"]) > 10

    def test_real_interpret_sii_function(self):
        """Тест реальной функции interpret_sii без моков"""
        # Тест для рака легкого с умеренным SII
        level, interpretation = interpret_sii(800.0, "C34")
        
        assert isinstance(level, SIILevel)
        assert isinstance(interpretation, str)
        assert len(interpretation) > 10
        
        # Для неизвестного типа рака
        level_unknown, interpretation_unknown = interpret_sii(800.0, "UNKNOWN")
        assert level_unknown == SIILevel.low
        assert interpretation_unknown == "Нормальный уровень" 