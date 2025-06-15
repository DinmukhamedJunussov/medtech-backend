from datetime import datetime
from typing import List, Tuple, Dict, Optional
import random

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from enum import Enum, IntEnum
from pydantic import BaseModel, Field

class SIILevel(str, Enum):
    very_low = "🔴 Очень низкий"
    low = "🟩 Низкий"
    moderate = "🟡 Умеренный"
    borderline_high = "🟠 Погранично-высокий"
    high = "🔴 Высокий"

    @classmethod
    def from_int(cls, value: int) -> "SIILevel":
        mapping = {
            1: cls.very_low,
            2: cls.low,
            3: cls.moderate,
            4: cls.borderline_high,
            5: cls.high,
        }
        if value not in mapping:
            raise ValueError(f"Invalid value {value}. Must be between 1 and 5.")
        return mapping[value]

class RiskLevel(IntEnum):
    """Уровни риска SII"""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5

class Recommendation(BaseModel):
    """Модель для одной рекомендации"""
    title: str = Field(..., description="Заголовок группы рекомендаций")
    items: List[str] = Field(..., description="Список конкретных рекомендаций")

class SIIConclusion(BaseModel):
    """Модель для заключения по уровню SII"""
    title: str = Field(..., description="Название уровня риска")
    description: str = Field(..., description="Описание состояния")
    recommendations: List[Recommendation] = Field(..., description="Список групп рекомендаций")

class SIIResult(BaseModel):
    sii: float
    level: SIILevel
    interpretation: str

class BloodTestResults(BaseModel):
    """Модель для хранения результатов анализа крови"""
    
    # Основные показатели
    hemoglobin: float | None = Field(None, description="Гемоглобин (HGB)")
    white_blood_cells: float | None = Field(None, description="Лейкоциты (WBC)")
    red_blood_cells: float | None = Field(None, description="Эритроциты (RBC)")
    platelets: float | None = Field(None, description="Тромбоциты (PLT)")
    
    # Нейтрофилы
    neutrophils_percent: float | None = Field(None, description="Нейтрофилы (NEUT%)")
    neutrophils_absolute: float | None = Field(None, description="Нейтрофилы (абс. кол-во) (NEUT#)")
    
    # Лимфоциты
    lymphocytes_percent: float | None = Field(None, description="Лимфоциты (LYM%)")
    lymphocytes_absolute: float | None = Field(None, description="Лимфоциты (абс. кол-во) (LYM#)")
    
    # Моноциты
    monocytes_percent: float | None = Field(None, description="Моноциты (MON%)")
    monocytes_absolute: float | None = Field(None, description="Моноциты (абс. кол-во) (MON#)")
    
    # Эозинофилы
    eosinophils_percent: float | None = Field(None, description="Эозинофилы (EOS%)")
    eosinophils_absolute: float | None = Field(None, description="Эозинофилы (абс. кол-во) (EOS#)")
    
    # Базофилы
    basophils_percent: float | None = Field(None, description="Базофилы (BAS%)")
    basophils_absolute: float | None = Field(None, description="Базофилы (абс. кол-во) (BAS#)")

    # Cancer type
    cancer_type: str | None = Field(None, description="Cancer type")

    model_config = {
        "json_schema_extra": {
            "example": {
                "hemoglobin": 14.5,
                "white_blood_cells": 6.8,
                "red_blood_cells": 4.5,
                "platelets": 250,
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
                "cancer_type": "C34",
            }
        }
    }

blood_test_names = [
    ("Гемоглобин", "HGB"),
    ("Лейкоциты", "WBC"),
    ("Эритроциты", "RBC"),
    ("Тромбоциты", "PLT"),
    ("Нейтрофилы", "NEUT%"),
    ("Нейтрофилы (абс. кол-во)", "NEUT#"),
    ("Лимфоциты", "LYM%"),
    ("Лимфоциты (абс. кол-во)", "LYM#"),
    ("Моноциты", "MON%"),
    ("Моноциты (абс. кол-во)", "MON#"),
    ("Эозинофилы", "EOS%"),
    ("Эозинофилы (абс. кол-во)", "EOS#"),
    ("Базофилы", "BAS%"),
    ("Базофилы (абс. кол-во)", "BAS#"),
]


class CancerType(BaseModel):
    id: int
    name: str
    sii_categories: List[Tuple[int, int | None]]
    justification: str
    references: List[str]
    icd10_codes: List[str]


cancer_types = [
    CancerType(
        id=1,
        name="Рак легкого (немелкоклеточный и мелкоклеточный)",
        sii_categories=[(0, 100), (100, 600), (600, 1000), (1000, 1500), (1500, 1000000000)],
        justification="Метаанализы показывают худший прогноз при SII > 1000–1200 у НМРЛ и > 900 у МРЛ.",
        references=["PMC6370019", "PMC8854201", "PMC9280894"],
        icd10_codes=["C34"]
    ),
    CancerType(
        id=2,
        name="Рак поджелудочной железы",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 1000), (1000, 1000000000)],
        justification="SII > 700–900 — фактор риска; подтверждено в метаанализах.",
        references=["PMC8436945", "PMC8329648"],
        icd10_codes=["C25"]
    ),
    CancerType(
        id=3,
        name="Рак желудка",
        sii_categories=[(0, 100), (100, 400), (400, 660), (661, 1000), (1000, 1000000000)],
        justification="SII > 660–800 ухудшает прогноз.",
        references=["PMC8918673", "PMC5650428"],
        icd10_codes=["C16"]
    ),
    CancerType(
        id=4,
        name="Рак пищевода",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, 1000000000)],
        justification="Границы 600–900 критические.",
        references=["PMC9459851", "PMC10289742", "PMC8487212"],
        icd10_codes=["C15"]
    ),
    CancerType(
        id=5,
        name="Колоректальный рак",
        sii_categories=[(0, 100), (100, 340), (340, 600), (601, 900), (900, 1000000000)],
        justification="SII > 900 после хирургии ухудшает выживаемость.",
        references=["JSTAGE (2023)", "PMC5650428"],
        icd10_codes=["C18", "C19", "C20"]
    ),
    CancerType(
        id=6,
        name="Рак молочной железы",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 800), (800, 1000000000)],
        justification="SII > 800 — худший прогноз.",
        references=["PMC7414550", "EuropeanReview", "PMC5650428"],
        icd10_codes=["C50"]
    ),
    CancerType(
        id=7,
        name="Гинекологические опухоли (яичник, шейка, эндометрий)",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 900), (900, 1000000000)],
        justification="Порог риска 600–700; >900 — негативный прогноз.",
        references=["PMC7414550", "PMC5650428"],
        icd10_codes=["C53", "C54", "C56"]
    ),
    CancerType(
        id=8,
        name="Гепатоцеллюлярная карцинома (ГЦК)",
        sii_categories=[(0, 100), (100, 330), (330, 600), (601, 900), (900, 1000000000)],
        justification="SII > 600 связан с рецидивом и плохой выживаемостью.",
        references=["Springer (2020)", "PMC5650428"],
        icd10_codes=["C22.0"]
    ),
    CancerType(
        id=9,
        name="Желчевыводящие пути (вкл. холангиокарцинома)",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, 1000000000)],
        justification="Пороги 600–900 демонстрируют значимые различия.",
        references=["PMC9691295", "PMC9519406"],
        icd10_codes=["C22.1", "C24"]
    ),
    CancerType(
        id=10,
        name="Простата",
        sii_categories=[(0, 100), (100, 500), (500, 800), (801, 1000), (1000, 1000000000)],
        justification="SII > 900 ухудшает прогноз.",
        references=["PMC9814343", "PMC9898902"],
        icd10_codes=["C61"]
    ),
    CancerType(
        id=11,
        name="Мочевой пузырь",
        sii_categories=[(0, 100), (100, 500), (500, 800), (801, 1000), (1000, 1000000000)],
        justification="Для урологических опухолей приняты значения 600–800.",
        references=["PMC8519535", "EuropeanReview"],
        icd10_codes=["C67"]
    ),
    CancerType(
        id=12,
        name="Почечно-клеточный рак (RCC)",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 1000), (1000, 1000000000)],
        justification="SII > 600–1000 — четкий фактор риска.",
        references=["Springer (2020)", "PMC5650428"],
        icd10_codes=["C64"]
    ),
    CancerType(
        id=13,
        name="Опухоли головы и шеи (в т.ч. носоглотка)",
        sii_categories=[(0, 100), (100, 450), (450, 600), (601, 800), (800, 1000000000)],
        justification="Порог 600–800 — значимое ухудшение прогноза.",
        references=["PMC9675963", "PMC5650428"],
        icd10_codes=["C00", "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12", "C13",
                     "C14", "C30", "C31", "C32"]
    ),
    CancerType(
        id=14,
        name="Глиобластома и глиомы",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, 1000000000)],
        justification="SII > 600–900 коррелирует с худшим прогнозом.",
        references=["PMC10340562"],
        icd10_codes=["C71"]
    ),
    CancerType(
        id=15,
        name="Насофарингеальная карцинома",
        sii_categories=[(0, 100), (100, 450), (450, 600), (601, 800), (800, 1000000000)],
        justification="Чем выше SII, тем хуже прогноз.",
        references=["PMC9675963"],
        icd10_codes=["C11"]
    ),
    CancerType(
        id=16,
        name="Рак кожи (меланома)",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, 1000000000)],
        justification="Паттерн снижения выживаемости при увеличении SII.",
        references=["PMC5650428"],
        icd10_codes=["C43"]
    ),
    CancerType(
        id=17,
        name="Саркомы мягких тканей",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, 1000000000)],
        justification="Универсальный паттерн в солидных опухолях.",
        references=["PMC5650428"],
        icd10_codes=["C49"]
    ),
    CancerType(
        id=18,
        name="Герминогенные опухоли (яички)",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 900), (900, 1000000000)],
        justification="Пороговые значения аналогичны простате и мочевому пузырю.",
        references=["PMC7552553"],
        icd10_codes=["C62"]
    ),
    CancerType(
        id=19,
        name="Эндометриальный рак",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 900), (900, 1000000000)],
        justification="Схожие границы в гинекологических метаанализах.",
        references=["PMC7414550"],
        icd10_codes=["C54"]
    ),
    CancerType(
        id=20,
        name="Овариальный рак",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 900), (900, 1000000000)],
        justification="Аналогично другим гинекологическим ракам.",
        references=["PMC7414550"],
        icd10_codes=["C56"]
    )
]

# Рефакторированная структура уровней риска SII
SII_CONCLUSIONS: Dict[RiskLevel, SIIConclusion] = {
    RiskLevel.VERY_LOW: SIIConclusion(
        title="Очень низкий риск",
        description=(
            "Мониторинг эффективности противоопухолевого иммунитета вашего организма. "
            "Возможные объяснения низкого значения:\n"
            "- Значительное снижение числа лейкоцитов/нейтрофилов или тромбоцитов (например, после химиотерапии или на фоне апластических состояний).\n"
            "- Некоторые лабораторные ошибки или специфические состояния обмена в организме.\n\n"
        ),
        recommendations=[Recommendation(
                title="Регулярное наблюдение",
                items=[
                    "Рекомендуем динамический мониторинг показателей крови и обязательно обратиться к врачу для выяснения причины таких изменений.",
                    "Важно: Изолированный низкий результат не всегда отражает опасное состояние — его нужно всегда рассматривать в контексте текущего лечения, самочувствия и других анализов."
                ]
            ),]
    ),
    
    RiskLevel.LOW: SIIConclusion(
        title="Низкий риск",
        description=(
            "Мониторинг эффективности противоопухолевого иммунитета вашего организма.\n"
            "Баланс между воспалением и иммунитетом считается нормальным. 📈 Прогноз благоприятный."
        ),
        recommendations=[
            Recommendation(
                title="Регулярное наблюдение",
                items=[
                    "Контрольный анализ крови рекомендуется делать раз в 3–4 недели.",
                    "Сохраняйте привычный образ жизни: физическая активность, полноценный сон, позитивный настрой.",
                    "Уделяйте внимание сбалансированному питанию — больше овощей, фруктов, цельных злаков."
                ]
            ),
            Recommendation(
                title="Образ жизни",
                items=[
                    "Регулярно делайте лабораторные обследования по графику, согласованному с врачом.",
                    "Продолжайте поддерживать активный образ жизни: ежедневные прогулки, умеренная физкультура.",
                    "Соблюдайте стандартный режим дня, высыпайтесь, избегайте хронического стресса."
                ]
            ),
            Recommendation(
                title="Лечение",
                items=[
                    "Контрольный анализ крови рекомендуется делать раз в 3–4 недели.",
                    "При отсутствии новых жалоб продолжается текущее лечение без изменений.",
                    "Не занимайтесь самолечением, не прибегайте к новым препаратам без разрешения врача."
                ]
            )
        ]
    ),
    
    RiskLevel.MODERATE: SIIConclusion(
        title="Средний риск (Пограничное состояние)",
        description=(
            "Мониторинг эффективности противоопухолевого иммунитета вашего организма.\n"
            "Умеренное воспаление и/или снижение иммунного ответа. Прогноз сомнительный: возможны осложнения, начало прогрессии или нестабильность состояния (запланируйте повторный анализ крови через 7–14 дней для динамического наблюдения).\n"
            "Рекомендации:\n"
        ),
        recommendations=[
            Recommendation(
                title="Медицинское наблюдение",
                items=[
                    "Обязательно проконсультируйтесь с лечащим врачом для оценки изменений и уточнения терапии.",
                    "Усиленно следите за текущими симптомами (температура, слабость, аппетит) и фиксируйте новые ощущения.",
                    "Проверяйте уровень холестерина и сахара – особенно если есть склонность к сердечно-сосудистым и метаболическим заболеваниям."
                ]
            ),
            Recommendation(
                title="Контроль состояния",
                items=[
                    "Запланируйте повторный анализ крови через 7–14 дней для динамического наблюдения.",
                    "В случае повышения показателей, обязательно обратитесь к лечащему врачу.",
                    "Пересмотрите схему режима дня, выделяйте больше времени на отдых и восстановление.",
                    "Возможно потребуется добавить контроль показателей биохимии крови."
                ]
            ),
            Recommendation(
                title="Профилактика",
                items=[
                    "Уделите внимание любым перенесенным инфекциям — долечивание их полностью.",
                    "Сообщайте доктору об изменениях аппетита, сна, веса – это может быть важно для раннего выявления осложнений болезни.",
                    "Откажитесь от жирной, жареной и сильно переработанной пищи."
                ]
            )
        ]
    ),
    
    RiskLevel.HIGH: SIIConclusion(
        title="Высокий риск (Тревожный уровень)",
        description=(
            "Высокий уровень воспаления и снижение иммунитета. Риск прогрессирования и осложнений.\n"
            "Рекомендации:\n"
        ),
        recommendations=[
            Recommendation(
                title="Срочные меры",
                items=[
                    "Срочно запишитесь на консультацию к онкологу или профильному специалисту.",
                    "Проведите углубленное дообследование: возможно потребуется КТ/МРТ, определение опухолевых маркеров.",
                    "Обязательный динамический контроль показателей крови и биохимии не реже 1 раза в неделю.",
                    "Советуйтесь с лечащим врачом по поводу любых изменений самочувствия или побочных эффектов терапии."
                ]
            ),
            Recommendation(
                title="Мониторинг",
                items=[
                    "Согласуйте с врачом режим дополнительных обследований — возможно потребуется более частый контроль анализов (не реже 1 раза в неделю).",
                    "Не принимайте дополнительных препаратов и добавок без назначения специалиста.",
                    "Информируйте врача о резких изменениях веса, температуры, появлении болей."
                ]
            ),
            Recommendation(
                title="Коррекция лечения",
                items=[
                    "Если вы сейчас находитесь на этапе лечения, обсудите с врачом вариант пересмотра схемы лечения: изменение дозировок, подключение поддерживающих препаратов.",
                    "Согласуйте с врачом режим дополнительных инструментально-лабораторных обследований (контроль показателей крови и биохимии не реже 1 раза в неделю).",
                    "Не занимайтесь самолечением — любые препараты должны назначаться только специалистом."
                ]
            )
        ]
    ),
    
    RiskLevel.VERY_HIGH: SIIConclusion(
        title="Очень высокий риск (Критический)",
        description=(
            "Критически высокий уровень воспаления и угнетение иммунитета. Максимальный риск ухудшения состояния.\n"
            "Рекомендации:\n"
        ),
        recommendations=[
            Recommendation(
                title="Экстренные меры",
                items=[
                    "Немедленная очная консультация у врача онколога",
                    "Проведение полного обследования для поиска причин воспаления и принятия решения о дальнейшем лечении или корректировке терапии.",
                    "Еженедельный, а по состоянию и чаще, мониторинг крови и биохимии.",
                    "Обеспечение круглосуточного наблюдения (в домашних условиях с помощью близких или в стационаре)."
                ]
            ),
            Recommendation(
                title="Интенсивное наблюдение",
                items=[
                    "Немедленная очная консультация у врача онколога",
                    "Еженедельный, а по состоянию и чаще, мониторинг крови и биохимии.",
                    "Введение индивидуального плана экстренных мер: что делать при повышении температуры, начале кровотечения и других опасных симптомах.",
                    "Используйте только специальное лечебное питание, согласованное с врачом."
                ]
            ),
            Recommendation(
                title="План действий",
                items=[
                    "Немедленная очная консультация у врача онколога",
                    "Еженедельный, а по состоянию и чаще, мониторинг крови и биохимии.",
                    "Регулярно контролируйте температуру тела и самочувствие, фиксируйте любые изменения.",
                    "Заранее обсудите с врачом план экстренных действий на случай ухудшения состояния."
                ]
            )
        ]
    )
}

# Функция для получения заключения по уровню риска
def get_sii_conclusion(risk_level: int) -> Optional[SIIConclusion]:
    """
    Получает заключение по уровню риска SII
    
    Args:
        risk_level: Уровень риска (1-5)
        
    Returns:
        Объект SIIConclusion или None если уровень некорректный
    """
    try:
        level = RiskLevel(risk_level)
        return SII_CONCLUSIONS.get(level)
    except ValueError:
        return None

def get_random_recommendation(risk_level: int) -> Optional[Dict]:
    """
    Получает случайную рекомендацию для заданного уровня риска
    
    Args:
        risk_level: Уровень риска (1-5)
        
    Returns:
        Словарь с title, summary и одной случайной рекомендацией
    """
    conclusion = get_sii_conclusion(risk_level)
    if not conclusion or not conclusion.recommendations:
        return {
            "title": conclusion.title if conclusion else "",
            "summary": conclusion.description if conclusion else "",
            "recommendation": None
        }
    
    # Выбираем случайную рекомендацию
    random_rec = random.choice(conclusion.recommendations)
    
    return {
        "title": conclusion.title,
        "summary": conclusion.description,
        "recommendation": {
            "title": random_rec.title,
            "items": random_rec.items
        }
    }

# Модифицированная версия для совместимости со старым API (возвращает случайную рекомендацию)
def get_sii_conclusion_levels():
    """
    Генерирует sii_conclusion_levels со случайными рекомендациями для каждого уровня
    """
    return {
        level.value: get_random_recommendation(level.value)
        for level in RiskLevel
    }

# Совместимость со старым API (теперь с случайными рекомендациями)
sii_conclusion_levels = get_sii_conclusion_levels()

def get_cancer_name(cancer_code: str) -> str:
    """
    Получает название типа рака по коду ICD-10 или по ID

    Args:
        cancer_code: Код типа рака (ICD-10) или ID

    Returns:
        Название типа рака или "Неизвестный тип рака"
    """
    # Пробуем найти по коду ICD-10
    for cancer in cancer_types:
        if cancer_code in cancer.icd10_codes:
            return cancer.name

    # Если не нашли по ICD-10, пробуем по ID
    try:
        cancer_id = int(cancer_code)
        for cancer in cancer_types:
            if cancer.id == cancer_id:
                return cancer.name
    except (ValueError, TypeError):
        pass

    # Если не нашли, возвращаем неизвестный тип
    return "Неизвестный тип рака"