import io
import re
from datetime import datetime
from typing import Optional

import fitz  # PyMuPDF
import pdfplumber
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from loguru import logger
from src.schemas.blood_results import BloodTestResults, SIILevel, cancer_types, sii_conclusion_levels

CBC_MAPPING = {
    "гемоглобин": "hemoglobin",
    "лейкоциты": "white_blood_cells",
    "эритроциты": "red_blood_cells",
    "тромбоциты": "platelets",
    "нейтрофилы (общ.число), %": "neutrophils_percent",
    "нейтрофилы, абс.": "neutrophils_absolute",
    "лимфоциты, %": "lymphocytes_percent",
    "лимфоциты, абс.": "lymphocytes_absolute",
    "моноциты, %": "monocytes_percent",
    "моноциты, абс.": "monocytes_absolute",
    "эозинофилы, %": "eosinophils_percent",
    "эозинофилы, абс.": "eosinophils_absolute",
    "базофилы, %": "basophils_percent",
    "базофилы, абс.": "basophils_absolute",
}

# Маппинг для Olymp Labs
OLYMP_CBC_MAPPING = {
    "гемоглобин": "hemoglobin",
    "лейкоциты": "white_blood_cells",
    "эритроциты": "red_blood_cells",
    "тромбоциты": "platelets",
    "нейтрофилы": "neutrophils_percent",
    "нейтрофилы абс.": "neutrophils_absolute",
    "лимфоциты": "lymphocytes_percent",
    "лимфоциты абс.": "lymphocytes_absolute",
    "моноциты": "monocytes_percent",
    "моноциты абс.": "monocytes_absolute",
    "эозинофилы": "eosinophils_percent",
    "эозинофилы абс.": "eosinophils_absolute",
    "базофилы": "basophils_percent",
    "базофилы абс.": "basophils_absolute",
}

def extract_text_pages(pdf_bytes: bytes) -> list[str]:
    pages = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt and txt.strip():
                    pages.append(txt)
    except Exception:
        pass
    if not pages:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                txt = page.get_text()
                if txt and txt.strip():
                    pages.append(txt)
        except Exception:
            pass
    return pages

def clean_float(val):
    # Accept "1.44", "0,44", "1.44*", " 1.44 ", "1.44 1.67 10.05.24"
    try:
        # take first float-looking part
        m = re.search(r"[-+]?\d*[\.,]\d+|\d+", val.replace(',', '.'))
        if m:
            return float(m.group(0))
        return None
    except Exception:
        return None

def detect_lab_type(pages: list[str]) -> str:
    """
    Определяет формат лаборатории на основе содержимого PDF
    
    Args:
        pages: Список строк с текстом из PDF
        
    Returns:
        str: "invitro" или "olymp"
    """
    for page in pages:
        page_lower = page.lower()
        if "инвитро" in page_lower or "invitro" in page_lower:
            return "invitro"
        if "олимп" in page_lower or "olymp" in page_lower:
            return "olymp"
    
    # По умолчанию предполагаем Invitro, так как это основной формат
    return "invitro"

def extract_meta(text: str) -> dict:
    """Извлекает метаданные из текста PDF, но возвращает только поля, существующие в BloodTestResults"""
    meta = {}
    
    # Извлекаем cancer_type если найден
    cancer_pattern = re.search(r"диагноз[:\s]+([A-Z]\d+)", text, re.IGNORECASE)
    if cancer_pattern:
        meta['cancer_type'] = cancer_pattern.group(1)
    
    return meta

CBC_PATTERNS = [
    ("hemoglobin",        r"Гемоглобин[^\d]*(\d+[\.,]\d+|\d+)", 0),
    ("white_blood_cells", r"Лейкоциты[^\d]*(\d+[\.,]\d+|\d+)", 0),
    ("red_blood_cells",   r"Эритроциты[^\d]*(\d+[\.,]\d+|\d+)", 0),
    ("platelets",         r"Тромбоциты[^\d]*(\d+[\.,]\d+|\d+)", 0),
    ("neutrophils_percent",     r"Нейтрофилы.*(%|проц)[^\d]*(\d+[\.,]\d+|\d+)", 2),
    ("neutrophils_percent",     r"Нейтрофилы\s*\(.*число.*\)\s*,?\s*(\d+[\.,]\d+|\d+)", 1),
    ("neutrophils_percent",     r"Нейтрофилы[^\n]*?([-\d\.,]+)\s*%[^\S\n]*", 1),
    # absolute matches: extract from "абс." lines. They may look like "Лимфоциты, абс. 1.44 1.67"
    ("neutrophils_absolute",    r"Нейтрофилы[,]?\s*абс\.[^\d]*(\d+[\.,]\d+|\d+)", 1),
    ("lymphocytes_percent",     r"Лимфоциты, %\s*(\d+[\.,]\d+|\d+)", 1),
    ("lymphocytes_absolute",    r"Лимфоциты[,]?\s*абс\.[^\d]*(\d+[\.,]\d+|\d+)", 1),
    ("monocytes_percent",       r"Моноциты, %\s*(\d+[\.,]\d+|\d+)", 1),
    ("monocytes_absolute",      r"Моноциты[,]?\s*абс\.[^\d]*(\d+[\.,]\d+|\d+)", 1),
    ("eosinophils_percent",     r"Эозинофилы, %\s*(\d+[\.,]\d+|\d+)", 1),
    ("eosinophils_absolute",    r"Эозинофилы[,]?\s*абс\.[^\d]*(\d+[\.,]\d+|\d+)", 1),
    ("basophils_percent",       r"Базофилы, %\s*(\d+[\.,]\d+|\d+)", 1),
    ("basophils_absolute",      r"Базофилы[,]?\s*абс\.[^\d]*(\d+[\.,]\d+|\d+)", 1),
]

def extract_cbc_values(pages: list[str]) -> dict:
    """
    For every page and every line, always split the line into tokens,
    find the analyte label by 'startswith', and take the FIRST NUMERIC value directly after (to the right).
    This robustly handles: 'Лимфоциты, абс. 1.44 1.67 10.05.24 ...'
    """
    result: dict[str, float] = {}
    
    # Определяем формат лаборатории
    lab_type = detect_lab_type(pages)
    logger.info(f"DEBUG: extract_cbc_values called with lab_type: {lab_type}")
    
    found_keys = set()
    
    # Специальная обработка для лаборатории Olymp в НАЧАЛЕ функции
    if lab_type == "olymp":
        logger.info("DEBUG: Processing Olymp lab in extract_cbc_values")
        # В Olymp формате значения часто указаны на следующей строке после названия параметра
        for text in pages:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                # Логируем каждую строку для отладки
                if any(keyword in line_lower for keyword in ['нейтрофил', 'лимфоцит', 'моноцит', 'эозинофил', 'базофил']):
                    logger.info(f"DEBUG: Found keyword line {i+1}: '{line_stripped}' -> '{line_lower}'")
                
                # Обработка процентных значений - поиск в строке, а не точное совпадение
                param_mapping = {
                    'нейтрофилы': 'neutrophils_percent',
                    'лимфоциты': 'lymphocytes_percent', 
                    'моноциты': 'monocytes_percent',
                    'эозинофилы': 'eosinophils_percent',
                    'базофилы': 'basophils_percent'
                }
                
                # Проверяем, содержит ли строка название параметра и процентное значение
                for param_name, field_name in param_mapping.items():
                    if field_name not in found_keys and param_name in line_lower and '%' in line:
                        logger.info(f"DEBUG: Processing {field_name} from line: '{line_stripped}'")
                        # Ищем процентное значение в той же строке
                        match = re.search(r'(\d+[.,]\d*)\s*%', line)
                        if match:
                            val = match.group(1).replace(',', '.')
                            try:
                                result[field_name] = float(val)
                                found_keys.add(field_name)
                                logger.info(f"DEBUG: Found {field_name} = {val}")
                            except:
                                pass
    
    # Map CBC fields to Russian analyte name (prefix)
    prefix_map = [
        ('hemoglobin', 'Гемоглобин'),
        ('white_blood_cells', 'Лейкоциты'),
        ('red_blood_cells', 'Эритроциты'),
        ('platelets', 'Тромбоциты'),
        ('neutrophils_percent', 'Нейтрофилы (общ.число), %'),
        ('neutrophils_absolute', 'Нейтрофилы, абс.'),
        ('lymphocytes_percent', 'Лимфоциты, %'),
        ('lymphocytes_absolute', 'Лимфоциты, абс.'),
        ('monocytes_percent', 'Моноциты, %'),
        ('monocytes_absolute', 'Моноциты, абс.'),
        ('eosinophils_percent', 'Эозинофилы, %'),
        ('eosinophils_absolute', 'Эозинофилы, абс.'),
        ('basophils_percent', 'Базофилы, %'),
        ('basophils_absolute', 'Базофилы, абс.')
    ]
    
    # Используем другой маппинг для Olymp
    if lab_type == "olymp":
        prefix_map = [
            ('hemoglobin', 'Гемоглобин'),
            ('white_blood_cells', 'Лейкоциты'),
            ('red_blood_cells', 'Эритроциты'),
            ('platelets', 'Тромбоциты'),
            ('neutrophils_percent', 'Нейтрофилы'),
            ('neutrophils_absolute', 'Нейтрофилы абс.'),
            ('lymphocytes_percent', 'Лимфоциты'),
            ('lymphocytes_absolute', 'Лимфоциты абс.'),
            ('monocytes_percent', 'Моноциты'),
            ('monocytes_absolute', 'Моноциты абс.'),
            ('eosinophils_percent', 'Эозинофилы'),
            ('eosinophils_absolute', 'Эозинофилы абс.'),
            ('basophils_percent', 'Базофилы'),
            ('basophils_absolute', 'Базофилы абс.')
        ]
    
    # For flexibility, also try alternative labels for fields
    alt_labels = {
        'neutrophils_percent': ['Нейтрофилы (общ.число), %', 'Нейтрофилы, %', 'Нейтрофилы %', 'Нейтрофилы'],
        'lymphocytes_absolute': ['Лимфоциты, абс.', 'Лимфоциты абс.', 'Лимфоциты, абс', 'Лимфоциты абс', 'Абсолютное число лимфоцитов'],
        'eosinophils_absolute': ['Эозинофилы, абс.', 'Эозинофилы абс.', 'Эозинофилы, абс', 'Эозинофилы абс', 'Абсолютное число эозинофилов'],
        'neutrophils_absolute': ['Нейтрофилы, абс.', 'Нейтрофилы абс.', 'Нейтрофилы, абс', 'Нейтрофилы абс', 'Абсолютное число нейтрофилов'],
        'monocytes_absolute': ['Моноциты, абс.', 'Моноциты абс.', 'Моноциты, абс', 'Моноциты абс', 'Абсолютное число моноцитов'],
        'basophils_absolute': ['Базофилы, абс.', 'Базофилы абс.', 'Базофилы, абс', 'Базофилы абс', 'Абсолютное число базофилов'],
    }
    
    # Шаблоны для Olymp лабораторий
    if lab_type == "olymp":
        alt_labels = {
            'neutrophils_percent': ['Нейтрофилы', 'Нейтрофилы %', 'Нейтрофилы, %'],
            'lymphocytes_absolute': ['Лимфоциты абс.', 'Лимфоциты абсол.', 'Лимфоциты, абс', 'Абсолютное число лимфоцитов'],
            'eosinophils_absolute': ['Эозинофилы абс.', 'Эозинофилы абсол.', 'Эозинофилы, абс', 'Абсолютное число эозинофилов'],
            'neutrophils_absolute': ['Нейтрофилы абс.', 'Нейтрофилы абсол.', 'Нейтрофилы, абс', 'Абсолютное число нейтрофилов'],
            'monocytes_absolute': ['Моноциты абс.', 'Моноциты абсол.', 'Моноциты, абс', 'Абсолютное число моноцитов'],
            'basophils_absolute': ['Базофилы абс.', 'Базофилы абсол.', 'Базофилы, абс', 'Абсолютное число базофилов'],
        }
    
    # Регулярные выражения для извлечения значений напрямую из текста
    direct_regex = {
        'lymphocytes_absolute': r"лимфоцит.*?\s*абс.*?(\d+[.,]\d+)",
        'eosinophils_absolute': r"[эе]озинофил.*?\s*абс.*?(\d+[.,]\d+)",
        'neutrophils_absolute': r"[нН]ейтрофил.*?\s*абс.*?(\d+[.,]\d+)",
        'monocytes_absolute': r"[мМ]оноцит.*?\s*абс.*?(\d+[.,]\d+)",
        'basophils_absolute': r"[бБ]азофил.*?\s*абс.*?(\d+[.,]\d+)",
    }
    
    # Добавляем специальные выражения для Olymp
    if lab_type == "olymp":
        olymp_regex = {
            'hemoglobin': r"(?:Гемоглобин|Hgb)\s*(?:[-=:]|)\s*(\d+(?:[.,]\d+)?)",
            'white_blood_cells': r"(?:Лейкоциты|WBC)\s*(?:[-=:]|)\s*(\d+(?:[.,]\d+)?)",
            'red_blood_cells': r"(?:Эритроциты|RBC)\s*(?:[-=:]|)\s*(\d+(?:[.,]\d+)?)",
            'platelets': r"(?:Тромбоциты|PLT)\s*(?:[-=:]|)\s*(\d+(?:[.,]\d+)?)",
            'lymphocytes_percent': r"(?:Лимфоциты|Lymph)\s*%?\s*(?:[-=:]|)\s*(\d+(?:[.,]\d+)?)",
            'monocytes_percent': r"(?:Моноциты|Mono)\s*%?\s*(?:[-=:]|)\s*(\d+(?:[.,]\d+)?)",
            'neutrophils_percent': r"(?:Нейтрофилы|Neu)\s*%?\s*(?:[-=:]|)\s*(\d+(?:[.,]\d+)?)",
            'eosinophils_percent': r"(?:Эозинофилы|Eo)\s*%?\s*(?:[-=:]|)\s*(\d+(?:[.,]\d+)?)",
            'basophils_percent': r"(?:Базофилы|Baso)\s*%?\s*(?:[-=:]|)\s*(\d+(?:[.,]\d+)?)",
        }
        direct_regex.update(olymp_regex)
    
    # Сначала попробуем извлечь значения с помощью регулярных выражений напрямую из текста
    for text in pages:
        for field, pattern in direct_regex.items():
            if field in found_keys:
                continue
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).replace(',', '.')
                try:
                    result[field] = float(val)
                    found_keys.add(field)
                except:
                    pass
    
    # Затем стандартный подход - по строкам и токенам
    for text in pages:
        lines = text.split('\n')
        for line in lines:
            tokens = [x for x in line.strip().split() if x]
            line_joined = ' '.join(tokens)
            for field, label in prefix_map:
                if field in found_keys:
                    continue
                # Alternative labels
                if field in alt_labels:
                    is_label = any(line_joined.lower().startswith(alt.lower()) for alt in alt_labels[field])
                else:
                    is_label = line_joined.lower().startswith(label.lower())
                if not is_label:
                    continue
                # remove the label from the start, then take the FIRST number
                after_label = line_joined[len(label):].strip()
                # after_label.tokens may start with "1.44 1.67 10.05.24..." => we want first float
                match = re.search(r"(\d+[.,]?\d*)", after_label)
                if match:
                    val = match.group(1).replace(',', '.')
                    try:
                        result[field] = float(val)
                        found_keys.add(field)
                    except:
                        pass

    # Дополнительная обработка для самых частых ошибок - если мы видим процент, но не видим абсолютное значение
    if 'lymphocytes_percent' in result and 'lymphocytes_absolute' not in result:
        for text in pages:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'лимфоцит' in line.lower() and '%' in line:
                    # Проверяем следующую строку после строки с процентами
                    if i + 1 < len(lines) and 'абс' in lines[i + 1].lower():
                        match = re.search(r"(\d+[.,]\d+)", lines[i + 1])
                        if match:
                            val = match.group(1).replace(',', '.')
                            try:
                                result['lymphocytes_absolute'] = float(val)
                            except:
                                pass
    
    if 'eosinophils_percent' in result and 'eosinophils_absolute' not in result:
        for text in pages:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'эозинофил' in line.lower() and '%' in line:
                    # Проверяем следующую строку после строки с процентами
                    if i + 1 < len(lines) and 'абс' in lines[i + 1].lower():
                        match = re.search(r"(\d+[.,]\d+)", lines[i + 1])
                        if match:
                            val = match.group(1).replace(',', '.')
                            try:
                                result['eosinophils_absolute'] = float(val)
                            except:
                                pass
    

    
    logger.info(f"DEBUG: Final result from extract_cbc_values: {result}")
    return result

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
        basophils_absolute=find(r"Базофилы, абс\.\s+(\d+[\.,]?\d*)\s*тыс/мкл")
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


def interpret_sii(sii: float, cancer_type: str | None = None) -> tuple[SIILevel, str]:
    for value in cancer_types:
        if cancer_type and cancer_type in value.icd10_codes:
            cnt = 0
            for category in value.sii_categories:
                cnt += 1
                if category[0] is not None and category[1] is not None and category[0] <= sii <= category[1]:
                    return (SIILevel.from_int(cnt), sii_conclusion_levels[cnt]["summary"])
    # Возвращаем значение по умолчанию, если ничего не найдено
    return (SIILevel.low, "Нормальный уровень")


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
