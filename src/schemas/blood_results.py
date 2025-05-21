from datetime import datetime
from typing import List, Tuple

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from enum import Enum
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

class BloodTestInput(BaseModel):
    neutrophils_absolute: float = Field(..., description="Absolute neutrophil count (×10⁹/L)")
    lymphocytes_absolute: float = Field(..., description="Absolute lymphocyte count (×10⁹/L)")
    platelets: float = Field(..., description="Platelet count (×10⁹/L)")

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
                "cancer_type": "Рак легкого (немелкоклеточный и мелкоклеточный)",
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
        sii_categories=[(0, 100), (100, 600), (600, 1000), (1000, 1500), (1500, None)],
        justification="Метаанализы показывают худший прогноз при SII > 1000–1200 у НМРЛ и > 900 у МРЛ.",
        references=["PMC6370019", "PMC8854201", "PMC9280894"],
        icd10_codes=["C34"]
    ),
    CancerType(
        id=2,
        name="Рак поджелудочной железы",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 1000), (1000, None)],
        justification="SII > 700–900 — фактор риска; подтверждено в метаанализах.",
        references=["PMC8436945", "PMC8329648"],
        icd10_codes=["C25"]
    ),
    CancerType(
        id=3,
        name="Рак желудка",
        sii_categories=[(0, 100), (100, 400), (400, 660), (661, 1000), (1000, None)],
        justification="SII > 660–800 ухудшает прогноз.",
        references=["PMC8918673", "PMC5650428"],
        icd10_codes=["C16"]
    ),
    CancerType(
        id=4,
        name="Рак пищевода",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, None)],
        justification="Границы 600–900 критические.",
        references=["PMC9459851", "PMC10289742", "PMC8487212"],
        icd10_codes=["C15"]
    ),
    CancerType(
        id=5,
        name="Колоректальный рак",
        sii_categories=[(0, 100), (100, 340), (340, 600), (601, 900), (900, None)],
        justification="SII > 900 после хирургии ухудшает выживаемость.",
        references=["JSTAGE (2023)", "PMC5650428"],
        icd10_codes=["C18", "C19", "C20"]
    ),
    CancerType(
        id=6,
        name="Рак молочной железы",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 800), (800, None)],
        justification="SII > 800 — худший прогноз.",
        references=["PMC7414550", "EuropeanReview", "PMC5650428"],
        icd10_codes=["C50"]
    ),
    CancerType(
        id=7,
        name="Гинекологические опухоли (яичник, шейка, эндометрий)",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 900), (900, None)],
        justification="Порог риска 600–700; >900 — негативный прогноз.",
        references=["PMC7414550", "PMC5650428"],
        icd10_codes=["C53", "C54", "C56"]
    ),
    CancerType(
        id=8,
        name="Гепатоцеллюлярная карцинома (ГЦК)",
        sii_categories=[(0, 100), (100, 330), (330, 600), (601, 900), (900, None)],
        justification="SII > 600 связан с рецидивом и плохой выживаемостью.",
        references=["Springer (2020)", "PMC5650428"],
        icd10_codes=["C22.0"]
    ),
    CancerType(
        id=9,
        name="Желчевыводящие пути (вкл. холангиокарцинома)",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, None)],
        justification="Пороги 600–900 демонстрируют значимые различия.",
        references=["PMC9691295", "PMC9519406"],
        icd10_codes=["C22.1", "C24"]
    ),
    CancerType(
        id=10,
        name="Простата",
        sii_categories=[(0, 100), (100, 500), (500, 800), (801, 1000), (1000, None)],
        justification="SII > 900 ухудшает прогноз.",
        references=["PMC9814343", "PMC9898902"],
        icd10_codes=["C61"]
    ),
    CancerType(
        id=11,
        name="Мочевой пузырь",
        sii_categories=[(0, 100), (100, 500), (500, 800), (801, 1000), (1000, None)],
        justification="Для урологических опухолей приняты значения 600–800.",
        references=["PMC8519535", "EuropeanReview"],
        icd10_codes=["C67"]
    ),
    CancerType(
        id=12,
        name="Почечно-клеточный рак (RCC)",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 1000), (1000, None)],
        justification="SII > 600–1000 — четкий фактор риска.",
        references=["Springer (2020)", "PMC5650428"],
        icd10_codes=["C64"]
    ),
    CancerType(
        id=13,
        name="Опухоли головы и шеи (в т.ч. носоглотка)",
        sii_categories=[(0, 100), (100, 450), (450, 600), (601, 800), (800, None)],
        justification="Порог 600–800 — значимое ухудшение прогноза.",
        references=["PMC9675963", "PMC5650428"],
        icd10_codes=["C00", "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12", "C13",
                     "C14", "C30", "C31", "C32"]
    ),
    CancerType(
        id=14,
        name="Глиобластома и глиомы",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, None)],
        justification="SII > 600–900 коррелирует с худшим прогнозом.",
        references=["PMC10340562"],
        icd10_codes=["C71"]
    ),
    CancerType(
        id=15,
        name="Насофарингеальная карцинома",
        sii_categories=[(0, 100), (100, 450), (450, 600), (601, 800), (800, None)],
        justification="Чем выше SII, тем хуже прогноз.",
        references=["PMC9675963"],
        icd10_codes=["C11"]
    ),
    CancerType(
        id=16,
        name="Рак кожи (меланома)",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, None)],
        justification="Паттерн снижения выживаемости при увеличении SII.",
        references=["PMC5650428"],
        icd10_codes=["C43"]
    ),
    CancerType(
        id=17,
        name="Саркомы мягких тканей",
        sii_categories=[(0, 100), (100, 400), (400, 600), (601, 900), (900, None)],
        justification="Универсальный паттерн в солидных опухолях.",
        references=["PMC5650428"],
        icd10_codes=["C49"]
    ),
    CancerType(
        id=18,
        name="Герминогенные опухоли (яички)",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 900), (900, None)],
        justification="Пороговые значения аналогичны простате и мочевому пузырю.",
        references=["PMC7552553"],
        icd10_codes=["C62"]
    ),
    CancerType(
        id=19,
        name="Эндометриальный рак",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 900), (900, None)],
        justification="Схожие границы в гинекологических метаанализах.",
        references=["PMC7414550"],
        icd10_codes=["C54"]
    ),
    CancerType(
        id=20,
        name="Овариальный рак",
        sii_categories=[(0, 100), (100, 400), (400, 700), (701, 900), (900, None)],
        justification="Аналогично другим гинекологическим ракам.",
        references=["PMC7414550"],
        icd10_codes=["C56"]
    )
]

sii_conclusion_levels = {
    1: {
        "title": "Очень низкий риск",
        "summary": (
            "Мониторинг эффективности противоопухолевого иммунитета вашего организма. "
            "Возможные объяснения низкого значения:\n"
            "- Значительное снижение числа лейкоцитов/нейтрофилов или тромбоцитов (например, после химиотерапии или на фоне апластических состояний).\n"
            "- Некоторые лабораторные ошибки или специфические состояния обмена в организме.\n"
            "Рекомендуем динамический мониторинг показателей крови и обязательно обратиться к врачу для выяснения причины таких изменений.\n"
            "Важно: Изолированный низкий результат не всегда отражает опасное состояние — его нужно всегда рассматривать в контексте текущего лечения, самочувствия и других анализов."
        ),
    },
    2: {
        "title": "Низкий риск",
        "summary": (
            "Мониторинг эффективности противоопухолевого иммунитета вашего организма.\n"
            "Баланс между воспалением и иммунитетом считается нормальным. 📈 Прогноз благоприятный.\n"
            "Рекомендации:\n"
            "- Контрольный анализ крови раз в 3–4 недели.\n"
            "- Поддержание привычного образа жизни: физическая активность, сон, питание, позитивный настрой.\n"
            "- Сбалансированное питание: овощи, фрукты, цельные злаки.\n"
            "- Лабораторные обследования по графику, согласованному с врачом.\n"
            "- Избегать самолечения и новых препаратов без разрешения врача."
        ),
    },
    3: {
        "title": "Средний риск (Пограничное состояние)",
        "summary": (
            "Умеренное воспаление и/или снижение иммунного ответа. Прогноз сомнительный: возможны осложнения, "
            "начало прогрессии или нестабильность состояния.\n"
            "Рекомендации:\n"
            "- Повторный анализ через 7–14 дней.\n"
            "- Консультация с лечащим врачом.\n"
            "- Следить за симптомами и самочувствием.\n"
            "- Контроль уровня холестерина и сахара.\n"
            "- Отказ от жирной и переработанной пищи.\n"
            "- Обращать внимание на аппетит, вес, сон, перенесённые инфекции."
        ),
    },
    4: {
        "title": "Высокий риск (Тревожный уровень)",
        "summary": (
            "Высокий уровень воспаления и снижение иммунитета. Риск прогрессирования и осложнений.\n"
            "Рекомендации:\n"
            "- Срочная консультация с онкологом.\n"
            "- Дообследование: КТ/МРТ, онкомаркеры.\n"
            "- Контроль крови и биохимии минимум раз в неделю.\n"
            "- Информировать врача о любых изменениях состояния.\n"
            "- Избегать самолечения.\n"
            "- Пересмотр схемы лечения при необходимости."
        ),
    },
    5: {
        "title": "Очень высокий риск (Критический)",
        "summary": (
            "Критически высокий уровень воспаления и угнетение иммунитета. Максимальный риск ухудшения состояния.\n"
            "Рекомендации:\n"
            "- Немедленная очная консультация у онколога.\n"
            "- Полное обследование.\n"
            "- Еженедельный (или чаще) мониторинг крови и биохимии.\n"
            "- Круглосуточное наблюдение.\n"
            "- Индивидуальный план экстренных действий.\n"
            "- Специальное лечебное питание.\n"
            "- Контроль температуры и самочувствия."
        ),
    }
}


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