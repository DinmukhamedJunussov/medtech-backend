from enum import Enum

from pydantic import BaseModel


class SIICategory(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    BORDERLINE_HIGH = "borderline_high"
    HIGH = "high"

class SIICategoryInfo(BaseModel):
    category: SIICategory
    min_value: float | None = None
    max_value: float | None = None
    description: str
    emoji: str
    status: str
    clinical_meaning: str

    @property
    def range_description(self) -> str:
        if self.min_value is None:
            return f"< {self.max_value}"
        elif self.max_value is None:
            return f"> {self.min_value}"
        return f"{self.min_value}-{self.max_value}"

# Определение категорий SII
SII_CATEGORIES = {
    SIICategory.VERY_LOW: SIICategoryInfo(
        category=SIICategory.VERY_LOW,
        max_value=300,
        description="Сбалансированное состояние",
        emoji="🟢",
        status="Очень низкий",
        clinical_meaning="Наиболее благоприятный профиль. Высокая иммунная активность, "
        "низкий воспалительный фон. Часто y здоровых лиц."
    ),
    SIICategory.LOW: SIICategoryInfo(
        category=SIICategory.LOW,
        min_value=300,
        max_value=450,
        description="Иммунный статус сохранён",
        emoji="🟩",
        status="Низкий",
        clinical_meaning="Признаков активного воспаления нет, хорошая прогностическая "
        "группа y онкопациентов."
    ),
    SIICategory.MODERATE: SIICategoryInfo(
        category=SIICategory.MODERATE,
        min_value=450,
        max_value=600,
        description="Потенциальная активация иммунной системы",
        emoji="🟡",
        status="Умеренный",
        clinical_meaning="Возможны субклинические воспалительные процессы. Необходим "
        "контроль и повторный анализ."
    ),
    SIICategory.BORDERLINE_HIGH: SIICategoryInfo(
        category=SIICategory.BORDERLINE_HIGH,
        min_value=600,
        max_value=750,
        description="Умеренное воспаление",
        emoji="🟠",
        status="Погранично-высокий",
        clinical_meaning="Ассоциирован c повышенным риском y онкологических и "
        "хронических больных. Может быть предиктором неблагоприятного исхода."
    ),
    SIICategory.HIGH: SIICategoryInfo(
        category=SIICategory.HIGH,
        min_value=750,
        description="Активное воспаление / иммунное истощение",
        emoji="🔴",
        status="Высокий",
        clinical_meaning="Высокий риск летальности, плохой ответ на химиотерапию "
        "и быстрый прогресс при онкопроцессах. Требует немедленного вмешательства."
    )
}

def get_sii_category(sii_value: float) -> SIICategoryInfo:
    """
    Определяет категорию SII на основе значения.
    
    Args:
        sii_value (float): Значение SII
        
    Returns:
        SIICategoryInfo: Информация o категории SII
    """
    category_range = [300, 450, 600, 750]

    if sii_value < category_range[0]:
        return SII_CATEGORIES[SIICategory.VERY_LOW]
    elif sii_value < category_range[1]:
        return SII_CATEGORIES[SIICategory.LOW]
    elif sii_value < category_range[2]:
        return SII_CATEGORIES[SIICategory.MODERATE]
    elif sii_value <= category_range[3]:
        return SII_CATEGORIES[SIICategory.BORDERLINE_HIGH]
    else:
        return SII_CATEGORIES[SIICategory.HIGH]
    