from datetime import datetime

from src.schemas.blood_results import SIILevel


def interpret_sii(sii: float) -> tuple[SIILevel, str]:
    if sii < 300:
        return (
            SIILevel.very_low,
            "Сбалансированное состояние. Наиболее благоприятный профиль. Высокая иммунная активность, низкий воспалительный фон."
        )
    elif 300 <= sii < 450:
        return (
            SIILevel.low,
            "Иммунный статус сохранён. Признаков активного воспаления нет, хорошая прогностическая группа у онкопациентов."
        )
    elif 450 <= sii < 600:
        return (
            SIILevel.moderate,
            "Потенциальная активация иммунной системы. Возможны субклинические воспалительные процессы. Необходим контроль."
        )
    elif 600 <= sii < 750:
        return (
            SIILevel.borderline_high,
            "Умеренное воспаление. Ассоциирован с повышенным риском у онкологических и хронических больных."
        )
    else:
        return (
            SIILevel.high,
            "Активное воспаление или иммунное истощение. Высокий риск летальности и плохой ответ на лечение. Требует немедленного вмешательства."
        )

def convert_lab_results(raw: dict) -> dict:
    return {
        "hemoglobin": round(raw.get("Гемоглобин", 0) / 9.5, 1),  # e.g. 138 → 14.5
        "white_blood_cells": round(raw.get("Лейкоциты", 0), 1),
        "red_blood_cells": round(raw.get("Эритроциты", 0), 1),
        "platelets": int(raw.get("Тромбоциты", 0)),

        "neutrophils_percent": int(round(raw.get("Нейтрофилы %", 0))),
        "neutrophils_absolute": round(raw.get("Нейтрофилы #", 0), 1),

        "lymphocytes_percent": int(round(raw.get("Лимфоциты %", 0))),
        "lymphocytes_absolute": round(raw.get("Лимфоциты #", 0), 1),

        "monocytes_percent": int(round(raw.get("Моноциты %", 0))),
        "monocytes_absolute": round(raw.get("Моноциты #", 0), 1),

        "eosinophils_percent": int(round(raw.get("Эозинофилы %", 0))),
        "eosinophils_absolute": round(raw.get("Эозинофилы #", 0), 1),

        "basophils_percent": int(round(raw.get("Базофилы %", 0))),
        "basophils_absolute": round(raw.get("Базофилы #", 0), 1),

        # Defaults / constants
        "lab_id": 1,
        "patient_id": 1,
        "test_date": datetime(2024, 3, 20, 10, 0, 0).isoformat(),
        "notes": "Нормальные показатели"
    }
