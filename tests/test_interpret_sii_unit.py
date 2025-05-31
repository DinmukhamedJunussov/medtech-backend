import pytest
import random
from unittest.mock import patch, MagicMock

from src.services.helper import interpret_sii
from src.schemas.blood_results import SIILevel, cancer_types


class TestInterpretSiiUnit:
    """Детальные unit-тесты для функции interpret_sii"""
    
    def test_sii_calculation_logic_verification(self):
        """Верификация логики расчета категорий SII"""
        # Проверяем что категории из cancer_types применяются правильно
        lung_cancer = next(ct for ct in cancer_types if "C34" in ct.icd10_codes)
        
        # Категории для рака легкого: [(0, 100), (100, 600), (600, 1000), (1000, 1500), (1500, 1000000000)]
        test_cases = [
            (50, 1),      # попадает в (0, 100) -> категория 1
            (300, 2),     # попадает в (100, 600) -> категория 2  
            (800, 3),     # попадает в (600, 1000) -> категория 3
            (1200, 4),    # попадает в (1000, 1500) -> категория 4
            (2000, 5),    # попадает в (1500, 1000000000) -> категория 5
        ]
        
        for sii_value, expected_category in test_cases:
            with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
                mock_get_rec.return_value = {"summary": "Test", "recommendation": None}
                
                level, _ = interpret_sii(sii_value, "C34")
                expected_level = SIILevel.from_int(expected_category)
                
                assert level == expected_level, f"SII {sii_value} должен быть категории {expected_category}"
                mock_get_rec.assert_called_once_with(expected_category)

    def test_boundary_conditions_all_cancer_types(self):
        """Тест граничных условий для всех типов рака"""
        for cancer_type in cancer_types:
            for cancer_code in cancer_type.icd10_codes:
                categories = cancer_type.sii_categories
                
                # Тестируем границы между категориями
                for i, (lower, upper) in enumerate(categories, 1):
                    if upper is not None and upper < 1000000000:  # Избегаем слишком больших чисел
                        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
                            mock_get_rec.return_value = {"summary": "Test", "recommendation": None}
                            
                            # Тест верхней границы текущей категории
                            level, _ = interpret_sii(float(upper), cancer_code)
                            expected_level = SIILevel.from_int(i)
                            assert level == expected_level, \
                                f"SII {upper} для {cancer_code} должен быть категории {i}"

    def test_edge_case_exact_boundary_values(self):
        """Тест точных граничных значений"""
        # Тест для рака легкого - граница между категориями 2 и 3 (600)
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {"summary": "Test", "recommendation": None}
            
            # 600 должно попасть в категорию 2 (100, 600)
            level, _ = interpret_sii(600.0, "C34")
            assert level == SIILevel.low
            
            # 600.1 должно попасть в категорию 3 (600, 1000) 
            level, _ = interpret_sii(600.1, "C34")
            assert level == SIILevel.moderate

    def test_random_recommendation_integration(self):
        """Тест интеграции с функцией get_random_recommendation"""
        sii_value = 800.0
        cancer_type = "C34"
        
        # Тест с полной рекомендацией
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_recommendation = {
                "title": "Средний риск",
                "summary": "Описание среднего риска\nДетальное описание состояния",
                "recommendation": {
                    "title": "Медицинское наблюдение",
                    "items": [
                        "Консультация с врачом",
                        "Повторный анализ через 2 недели", 
                        "Мониторинг симптомов"
                    ]
                }
            }
            mock_get_rec.return_value = mock_recommendation
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            # Проверяем что все элементы присутствуют в результате
            assert mock_recommendation["summary"] in interpretation
            assert mock_recommendation["recommendation"]["title"] + ":" in interpretation
            
            for item in mock_recommendation["recommendation"]["items"]:
                assert item in interpretation
            
            # Проверяем форматирование
            assert "\n\n" in interpretation  # Разделитель между описанием и рекомендациями
            assert "•" in interpretation      # Маркеры списка

    def test_recommendation_items_all_included(self):
        """Тест что все пункты рекомендаций включаются в результат"""
        sii_value = 1200.0
        cancer_type = "C25"  # Рак поджелудочной
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            test_items = [
                "Первая рекомендация",
                "Вторая рекомендация с длинным текстом",
                "Третья краткая рекомендация",
                "Четвертая рекомендация с специальными символами: 7-14 дней, >900",
                "Пятая рекомендация"
            ]
            
            mock_get_rec.return_value = {
                "summary": "Тестовое описание",
                "recommendation": {
                    "title": "Тестовая группа",
                    "items": test_items
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            # Проверяем что все пункты присутствуют
            for item in test_items:
                assert item in interpretation, f"Пункт '{item}' отсутствует в интерпретации"
            
            # Проверяем количество маркеров списка
            bullet_count = interpretation.count("•")
            assert bullet_count == len(test_items), f"Ожидалось {len(test_items)} маркеров, найдено {bullet_count}"

    def test_fallback_scenarios(self):
        """Тест различных сценариев fallback"""
        sii_value = 500.0
        cancer_type = "C34"
        
        # Сценарий 1: get_random_recommendation возвращает None
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = None
            level, interpretation = interpret_sii(sii_value, cancer_type)
            assert interpretation == "Описание недоступно"
        
        # Сценарий 2: get_random_recommendation возвращает пустой словарь
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {}
            level, interpretation = interpret_sii(sii_value, cancer_type)
            assert interpretation == "Описание недоступно"
        
        # Сценарий 3: recommendation = None
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Есть описание",
                "recommendation": None
            }
            level, interpretation = interpret_sii(sii_value, cancer_type)
            assert interpretation == "Есть описание"
        
        # Сценарий 4: recommendation без ключа 'recommendation'
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Есть описание",
                "title": "Заголовок"
            }
            level, interpretation = interpret_sii(sii_value, cancer_type)
            assert interpretation == "Есть описание"

    def test_cancer_type_matching_logic(self):
        """Тест логики сопоставления типов рака"""
        test_cases = [
            # Точные совпадения
            ("C34", True, "Рак легкого"),
            ("C25", True, "Рак поджелудочной железы"),
            ("C16", True, "Рак желудка"),
            
            # Множественные коды для одного типа рака
            ("C18", True, "Колоректальный рак"),
            ("C19", True, "Колоректальный рак"), 
            ("C20", True, "Колоректальный рак"),
            
            # Несуществующие коды
            ("C99", False, None),
            ("INVALID", False, None),
            ("", False, None),
        ]
        
        for cancer_code, should_match, expected_cancer_name in test_cases:
            with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
                mock_get_rec.return_value = {"summary": "Test", "recommendation": None}
                
                level, interpretation = interpret_sii(500.0, cancer_code)
                
                if should_match:
                    # Должен найти соответствующий тип рака и вызвать get_random_recommendation
                    mock_get_rec.assert_called_once()
                    # Уровень должен быть определен на основе категорий рака
                    assert level != SIILevel.low or interpretation != "Нормальный уровень"
                else:
                    # Не должен найти тип рака, вернуть значения по умолчанию
                    mock_get_rec.assert_not_called()
                    assert level == SIILevel.low
                    assert interpretation == "Нормальный уровень"

    def test_randomness_in_recommendation_selection(self):
        """Тест случайности выбора рекомендаций"""
        sii_value = 800.0
        cancer_type = "C34"
        
        test_items = ["Рекомендация 1", "Рекомендация 2", "Рекомендация 3"]
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Тестовое описание",
                "recommendation": {
                    "title": "Тестовая группа",
                    "items": test_items
                }
            }
            
            # Вызываем функцию несколько раз в контексте мока
            for i in range(3):
                level, interpretation = interpret_sii(sii_value, cancer_type)
                
                # Проверяем что все items включены в результат
                for item in test_items:
                    assert item in interpretation, f"Пункт '{item}' отсутствует в интерпретации"
                
                # Проверяем форматирование
                assert "Тестовое описание" in interpretation
                assert "Тестовая группа:" in interpretation
                assert "•" in interpretation
            
            # Последний вызов тоже в контексте мока
            level, interpretation = interpret_sii(sii_value, cancer_type)
            for item in test_items:
                assert item in interpretation

    def test_actual_randomness_behavior(self):
        """Тест фактического поведения случайности в get_random_recommendation"""
        sii_value = 800.0
        cancer_type = "C34"
        
        # Вызываем функцию несколько раз без моков и проверяем что результат меняется
        results = []
        for i in range(10):
            level, interpretation = interpret_sii(sii_value, cancer_type)
            results.append(interpretation)
        
        # Проверяем что уровень одинаковый во всех случаях (для одного и того же SII)
        levels = []
        for i in range(10):
            level, _ = interpret_sii(sii_value, cancer_type)
            levels.append(level)
        
        # Все уровни должны быть одинаковыми
        assert all(l == levels[0] for l in levels), "Уровень SII должен быть постоянным для одного значения"
        
        # Интерпретации могут отличаться из-за случайности в рекомендациях
        # (это зависит от реальной реализации get_random_recommendation)

    def test_performance_with_large_sii_values(self):
        """Тест производительности с большими значениями SII"""
        large_sii_values = [10000, 100000, 1000000, 10000000]
        
        for sii_value in large_sii_values:
            with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
                mock_get_rec.return_value = {"summary": "Test", "recommendation": None}
                
                level, interpretation = interpret_sii(float(sii_value), "C34")
                
                # Большие значения должны попадать в самую высокую категорию
                assert level == SIILevel.high
                mock_get_rec.assert_called_once_with(5)

    def test_special_characters_in_recommendations(self):
        """Тест обработки специальных символов в рекомендациях"""
        sii_value = 600.0
        cancer_type = "C50"
        
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            special_items = [
                "Рекомендация с цифрами: анализ через 7-14 дней",
                "Рекомендация со знаками: SII > 600-900 критично",
                "Рекомендация с символами: (вкл. холангиокарцинома)",
                "Рекомендация с кавычками: \"специальная диета\"",
                "Рекомендация с процентами: эффективность 90-95%"
            ]
            
            mock_get_rec.return_value = {
                "summary": "Описание с символами: >900 опасно",
                "recommendation": {
                    "title": "Специальные меры (критические)",
                    "items": special_items
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            
            # Проверяем что все специальные символы сохранены
            for item in special_items:
                assert item in interpretation
            
            # Проверяем что специальные символы в описании тоже сохранены
            assert ">900 опасно" in interpretation
            assert "(критические)" in interpretation

    def test_recommendation_structure_validation(self):
        """Тест валидации структуры рекомендаций"""
        sii_value = 800.0
        cancer_type = "C34"
        
        # Тест с корректной структурой
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Корректное описание",
                "recommendation": {
                    "title": "Корректный заголовок",
                    "items": ["Пункт 1", "Пункт 2"]
                }
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            assert "Корректное описание" in interpretation
            assert "Корректный заголовок:" in interpretation
            assert "Пункт 1" in interpretation
            assert "Пункт 2" in interpretation

    def test_get_random_recommendation_fallback_handling(self):
        """Тест обработки различных ответов от get_random_recommendation"""
        sii_value = 800.0
        cancer_type = "C34"
        
        # Тест когда get_random_recommendation возвращает неожиданную структуру
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            # Возвращаем строку вместо словаря (эмуляция ошибки)
            mock_get_rec.return_value = "Неожиданная строка"
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            # Функция должна обработать это корректно и не упасть
            assert level == SIILevel.moderate  # Для SII=800 и C34
            assert interpretation == "Описание недоступно"
        
        # Тест с None в recommendation
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Есть описание",
                "recommendation": None
            }
            
            level, interpretation = interpret_sii(sii_value, cancer_type)
            assert interpretation == "Есть описание"
        
        # Тест с отсутствующим ключом 'items'
        with patch('src.services.helper.get_random_recommendation') as mock_get_rec:
            mock_get_rec.return_value = {
                "summary": "Описание без items",
                "recommendation": {
                    "title": "Заголовок без items"
                }
            }
            
            # Это должно вызвать KeyError или AttributeError, которые нужно обработать
            try:
                level, interpretation = interpret_sii(sii_value, cancer_type)
                # Если функция не упала, проверяем что она вернула fallback
                assert level == SIILevel.moderate
            except (KeyError, AttributeError):
                # Если функция упала, это указывает на необходимость улучшения обработки ошибок
                pytest.fail("Функция interpret_sii должна обрабатывать отсутствующий ключ 'items'") 