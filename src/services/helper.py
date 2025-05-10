import io
import re
from datetime import datetime
from typing import Optional

import fitz  # PyMuPDF
import pdfplumber
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from src.schemas.blood_results import BloodTestResults, SIILevel


def clean_number(value: str) -> Optional[float]:
    if value is None:
        return None
    value = value.replace(',', '.')
    try:
        return float(value)
    except ValueError:
        return None

def parse_results(text: str) -> BloodTestResults:
    def find(pattern):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return clean_number(match.group(1)) if match else None

    def find_date(pattern):
        match = re.search(pattern, text)
        if match:
            try:
                # format: 01.06.2024 09:03
                return datetime.strptime(match.group(1), "%d.%m.%Y %H:%M")
            except Exception:
                return None
        return None

    return BloodTestResults(
        hemoglobin=find(r"Гемоглобин\s+(\d+[\.,]?\d*)\s*г/л"),
        white_blood_cells=find(r"Лейкоциты\s+(\d+[\.,]?\d*)\s*тыс/мкл"),
        red_blood_cells=find(r"Эритроциты\s+(\d+[\.,]?\d*)\s*млн/мкл"),
        platelets=find(r"Тромбоциты\s+(\d+[\.,]?\d*)\s*тыс/мкл"),
        neutrophils_percent=find(r"Нейтрофилы.*?(\d+[\.,]?\d*)\*?\s*%"),
        neutrophils_absolute=find(r"Нейтрофилы, абс\.\s+(\d+[\.,]?\d*)\s*тыс/мкл"),
        lymphocytes_percent=find(r"Лимфоциты, %\s+(\d+[\.,]?\d*)\*?\s*%"),
        lymphocytes_absolute=find(r"Лимфоциты, абс\.\s+(\d+[\.,]?\d*)\s*тыс/мкл"),
        monocytes_percent=find(r"Моноциты, %\s+(\d+[\.,]?\d*)\s*%"),
        monocytes_absolute=find(r"Моноциты, абс\.\s+(\d+[\.,]?\d*)\s*тыс/мкл"),
        eosinophils_percent=find(r"Эозинофилы, %\s+(\d+[\.,]?\d*)\s*%"),
        eosinophils_absolute=find(r"Эозинофилы, абс\.\s+(\d+[\.,]?\d*)\s*тыс/мкл"),
        basophils_percent=find(r"Базофилы, %\s+(\d+[\.,]?\d*)\s*%"),
        basophils_absolute=find(r"Базофилы, абс\.\s+(\d+[\.,]?\d*)\s*тыс/мкл"),
        test_date=find_date(r'Үлгі алынған күні.*?(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})')
    )

def extract_text_pdfplumber(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or '' for page in pdf.pages)

def extract_text_fitz(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    result = ""
    for page in doc:
        result += page.get_text()
    return result

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
