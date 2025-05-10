import os
import pytest

from src.services.helper import extract_cbc_values, detect_lab_type

class TestBloodParserHelper:
    
    def test_detect_invitro_lab(self):
        """Проверка определения лаборатории Invitro по тексту"""
        pages = ["Результаты анализов ИНВИТРО", "Другой текст"]
        assert detect_lab_type(pages) == "invitro"
        
        pages = ["Результаты анализов invitro", "Другой текст"]
        assert detect_lab_type(pages) == "invitro"
    
    def test_detect_olymp_lab(self):
        """Проверка определения лаборатории Olymp по тексту"""
        pages = ["Результаты анализов ОЛИМП", "Другой текст"]
        assert detect_lab_type(pages) == "olymp"
        
        pages = ["Результаты анализов olymp", "Другой текст"]
        assert detect_lab_type(pages) == "olymp"
        
        pages = ["Результаты анализов олимп", "Другой текст"]
        assert detect_lab_type(pages) == "olymp"
    
    def test_extract_cbc_values_invitro(self):
        """Тест парсинга значений из Invitro формата"""
        pages = [
            """
            Гемоглобин 145 г/л
            Лейкоциты 6.8 x10^9/л
            Эритроциты 4.5 x10^12/л
            Тромбоциты 250 x10^9/л
            Нейтрофилы (общ.число), % 60.0 %
            Нейтрофилы, абс. 4.1 x10^9/л
            Лимфоциты, % 30.0 %
            Лимфоциты, абс. 2.0 x10^9/л
            Моноциты, % 5.0 %
            Моноциты, абс. 0.3 x10^9/л
            Эозинофилы, % 3.0 %
            Эозинофилы, абс. 0.2 x10^9/л
            Базофилы, % 2.0 %
            Базофилы, абс. 0.1 x10^9/л
            """
        ]
        
        results = extract_cbc_values(pages)
        
        assert results["hemoglobin"] == 145.0
        assert results["white_blood_cells"] == 6.8
        assert results["red_blood_cells"] == 4.5
        assert results["platelets"] == 250.0
        assert results["neutrophils_percent"] == 60.0
        assert results["neutrophils_absolute"] == 4.1
        assert results["lymphocytes_percent"] == 30.0
        assert results["lymphocytes_absolute"] == 2.0
        assert results["monocytes_percent"] == 5.0
        assert results["monocytes_absolute"] == 0.3
        assert results["eosinophils_percent"] == 3.0
        assert results["eosinophils_absolute"] == 0.2
        assert results["basophils_percent"] == 2.0
        assert results["basophils_absolute"] == 0.1
    
    def test_extract_cbc_values_olymp(self):
        """Тест парсинга значений из Olymp формата"""
        pages = [
            """
            ОЛИМП Лаборатория
            
            Гематологический анализ крови
            
            Гемоглобин: 142 г/л
            Лейкоциты: 7.6 10^9/л
            Эритроциты: 4.8 10^12/л
            Тромбоциты: 230 10^9/л
            Нейтрофилы: 58.0 %
            Нейтрофилы абс.: 4.4 10^9/л
            Лимфоциты: 32.0 %
            Лимфоциты абс.: 2.4 10^9/л
            Моноциты: 6.0 %
            Моноциты абс.: 0.46 10^9/л
            Эозинофилы: 3.5 %
            Эозинофилы абс.: 0.27 10^9/л
            Базофилы: 0.5 %
            Базофилы абс.: 0.04 10^9/л
            """
        ]
        
        results = extract_cbc_values(pages)
        
        assert results["hemoglobin"] == 142.0
        assert results["white_blood_cells"] == 7.6
        assert results["red_blood_cells"] == 4.8
        assert results["platelets"] == 230.0
        assert results["neutrophils_percent"] == 58.0
        assert results["neutrophils_absolute"] == 4.4
        assert results["lymphocytes_percent"] == 32.0
        assert results["lymphocytes_absolute"] == 2.4
        assert results["monocytes_percent"] == 6.0
        assert results["monocytes_absolute"] == 0.46
        assert results["eosinophils_percent"] == 3.5
        assert results["eosinophils_absolute"] == 0.27
        assert results["basophils_percent"] == 0.5
        assert results["basophils_absolute"] == 0.04 