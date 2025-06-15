"""
Сервис для расчета индекса системного иммунного воспаления (SII)
"""
from typing import Optional, Tuple
from loguru import logger

from app.core.exceptions import SIICalculationError
from app.schemas.blood_results import BloodTestResults, SIILevel, SIIResult
from app.services.helper import interpret_sii


class SIICalculator:
    """Калькулятор для индекса системного иммунного воспаления"""
    
    def calculate_sii(self, data: BloodTestResults) -> SIIResult:
        """
        Рассчитывает SII индекс
        
        Args:
            data: Данные анализа крови
            
        Returns:
            SIIResult: Результат расчета SII
            
        Raises:
            SIICalculationError: При ошибке в расчете
        """
        try:
            # Проверяем наличие необходимых значений
            self._validate_required_values(data)
            
            # Рассчитываем SII (теперь мы уверены, что значения не None)
            assert data.neutrophils_absolute is not None
            assert data.platelets is not None
            assert data.lymphocytes_absolute is not None
            
            sii = (data.neutrophils_absolute * data.platelets) / data.lymphocytes_absolute
            
            # Интерпретируем результат
            level, interpretation = interpret_sii(sii, data.cancer_type)
            
            logger.info(f"Calculated SII: {sii:.2f}, Level: {level}, Cancer type: {data.cancer_type}")
            
            return SIIResult(
                sii=round(sii, 2),
                level=level,
                interpretation=interpretation
            )
            
        except Exception as e:
            logger.error(f"Error calculating SII: {str(e)}")
            raise SIICalculationError(f"SII calculation failed: {str(e)}")
    
    def _validate_required_values(self, data: BloodTestResults) -> None:
        """
        Проверяет наличие всех необходимых значений для расчета SII
        
        Args:
            data: Данные анализа крови
            
        Raises:
            SIICalculationError: При отсутствии необходимых данных
        """
        missing_fields = []
        
        if data.neutrophils_absolute is None:
            missing_fields.append("neutrophils_absolute")
        
        if data.platelets is None:
            missing_fields.append("platelets")
        
        if data.lymphocytes_absolute is None:
            missing_fields.append("lymphocytes_absolute")
        
        if missing_fields:
            raise SIICalculationError(f"Missing required fields for SII calculation: {', '.join(missing_fields)}")
        
        if data.lymphocytes_absolute == 0:
            raise SIICalculationError("Lymphocytes absolute count cannot be zero")
        
        # Проверяем на разумные значения (теперь с проверкой на None)
        if data.neutrophils_absolute is not None and data.neutrophils_absolute <= 0:
            raise SIICalculationError("Neutrophils absolute count must be positive")
        
        if data.platelets is not None and data.platelets <= 0:
            raise SIICalculationError("Platelets count must be positive")
    
    def get_sii_risk_assessment(self, sii_value: float, cancer_type: Optional[str] = None) -> dict:
        """
        Возвращает детальную оценку риска на основе SII
        
        Args:
            sii_value: Значение SII
            cancer_type: Тип рака (опционально)
            
        Returns:
            dict: Детальная оценка риска
        """
        level, interpretation = interpret_sii(sii_value, cancer_type)
        
        # Определяем числовой уровень риска
        risk_levels = {
            SIILevel.very_low: 1,
            SIILevel.low: 2,
            SIILevel.moderate: 3,
            SIILevel.borderline_high: 4,
            SIILevel.high: 5
        }
        
        risk_number = risk_levels.get(level, 3)
        
        return {
            "sii_value": round(sii_value, 2),
            "level": level,
            "risk_number": risk_number,
            "interpretation": interpretation,
            "cancer_type": cancer_type,
            "recommendations": self._get_recommendations_by_level(risk_number)
        }
    
    def _get_recommendations_by_level(self, risk_level: int) -> list:
        """Возвращает рекомендации по уровню риска"""
        recommendations = {
            1: [
                "Продолжайте регулярные профилактические обследования",
                "Поддерживайте здоровый образ жизни",
                "Контролируйте показатели крови каждые 6-12 месяцев"
            ],
            2: [
                "Рекомендуется контроль показателей каждые 6 месяцев",
                "Поддерживайте активный образ жизни",
                "Следите за питанием и сном"
            ],
            3: [
                "Необходим контроль показателей каждые 3-6 месяцев",
                "Рекомендуется консультация с онкологом",
                "Уделите внимание противовоспалительной диете"
            ],
            4: [
                "Требуется регулярный мониторинг каждые 3 месяца",
                "Обязательная консультация с онкологом",
                "Рассмотрите дополнительные обследования"
            ],
            5: [
                "Немедленная консультация с онкологом",
                "Ежемесячный контроль показателей",
                "Требуется комплексное обследование"
            ]
        }
        
        return recommendations.get(risk_level, recommendations[3]) 