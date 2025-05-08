import ast
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Optional, Tuple

import fitz  # PyMuPDF
import pdfplumber
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from mangum import Mangum
from openai import AsyncOpenAI
from rapidfuzz import process

from src.middlewares import monitor_service
from src.models.llm import system_prompt
from src.schemas.blood_results import (
    BloodTestInput,
    BloodTestResults,
    SIIResult,
    blood_test_names,
)
from src.services.helper import convert_lab_results, interpret_sii
from src.services.ocr_aws import analyze_document
from src.services.sii_category import get_sii_category
from src.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting up...")
    yield
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)
# Allow your frontend origin (e.g., http://localhost:3000)
origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://medtech-frontend.vercel.app",
    "https://medtech-frontend.vercel.app",
    "http://www.oncotest.kz",
    "https://www.oncotest.kz",
    "http://oncotest.kz",
    "https://oncotest.kz"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],  # or specify ["GET", "POST"]
    allow_headers=["*"],  # or specify ["Authorization", "Content-Type"]
)

app.middleware("http")(monitor_service)

async_client = AsyncOpenAI(api_key=settings.openai_api_key)

handler = Mangum(app)

@app.get("/")
def read_root():
    return {"Fact": "Dimash, you are doing great. Just imagine what you can achieve, if you continue putting effort "
                     "every day for the next 30 years"}

# def extract_values(text: str) -> Dict[str, str]:
#     patterns = {
#         "Гемоглобин": r"Гемоглобин\s+(\d+)\s+г/л",
#         "Лейкоциты": r"Лейкоциты\s+([\d,]+)\s+\*10\^9/л",
#         "Эритроциты": r"Эритроциты\s+([\d,]+)\s+\*10\^12/л",
#         "Тромбоциты": r"Тромбоциты\s+(\d+)\s+\*10\^9/л",
#         "Нейтрофилы %": r"Нейтрофилы\s+([\d,]+)\s+%",
#         "Нейтрофилы #": r"Нейтрофилы \(абс\. кол-во\)\s+([\d,]+)\s+\*10\^9/л",
#         "Лимфоциты %": r"Лимфоциты\s+([\d,]+)\s+%",
#         "Лимфоциты #": r"Лимфоциты \(абс\. кол-во\)\s+([\d,]+)\s+\*10\^9/л",
#         "Моноциты %": r"Моноциты\s+([\d,]+)\s+%",
#         "Моноциты #": r"Моноциты \(абс\. кол-во\)\s+([\d,]+)\s+\*10\^9/л",
#         "Эозинофилы %": r"Эозинофилы\s+([\d,]+)\s+%",
#         "Эозинофилы #": r"Эозинофилы \(абс\. кол-во\)\s+([\d,]+)\s+\*10\^9/л",
#         "Базофилы %": r"Базофилы\s+([\d,]+)\s+%",
#         "Базофилы #": r"Базофилы \(абс\. кол-во\)\s+([\d,]+)\s+\*10\^9/л",
#     }
#
#     results = {}
#     for key, pattern in patterns.items():
#         match = re.search(pattern, text)
#         results[key] = match.group(1).replace(",", ".") if match else None
#     return results
#
# @app.post("/parse-blood-test/")
# async def parse_blood_test(file: UploadFile = File(...)):
#     contents = await file.read()
#     with fitz.open(stream=contents, filetype="pdf") as doc:
#         full_text = "\n".join(page.get_text() for page in doc)
#     values = extract_values(full_text)
#     return values

BLOOD_TEST_MAP = {
    "hemoglobin": r"Гемоглобин\s+[A-Z]*\s*([\d.,]+)",
    "white_blood_cells": r"Лейкоциты\s+[A-Z]*\s*([\d.,]+)",
    "red_blood_cells": r"Эритроциты\s+[A-Z]*\s*([\d.,]+)",
    "platelets": r"Тромбоциты\s+[A-Z]*\s*([\d.,]+)",
    "neutrophils_percent": r"Нейтрофилы\s*NEU%\s*([\d.,]+)",
    "neutrophils_absolute": r"Нейтрофилы\s*\(абс. кол-во\)\s*NEU#\s*([\d.,]+)",
    "lymphocytes_percent": r"Лимфоциты\s*LYM%\s*([\d.,]+)",
    "lymphocytes_absolute": r"Лимфоциты\s*\(абс. кол-во\)\s*LYM#\s*([\d.,]+)",
    "monocytes_percent": r"Моноциты\s*MON%\s*([\d.,]+)",
    "monocytes_absolute": r"Моноциты\s*\(абс. кол-во\)\s*MON#\s*([\d.,]+)",
    "eosinophils_percent": r"Эозинофилы\s*EOS%\s*([\d.,]+)",
    "eosinophils_absolute": r"Эозинофилы\s*\(абс. кол-во\)\s*EOS#\s*([\d.,]+)",
    "basophils_percent": r"Базофилы\s*BAS%\s*([\d.,]+)",
    "basophils_absolute": r"Базофилы\s*\(абс. кол-во\)\s*BAS#\s*([\d.,]+)",
}

def extract_values(text: str):
    result = {}
    for parameter, pattern in BLOOD_TEST_MAP.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1).replace(",", ".")
            try:
                value = float(value)
            except ValueError:
                pass
            result[parameter] = value
        else:
            result[parameter] = None
    return result

@app.post("/parse-blood-test/")
async def parse_blood_test(file: UploadFile = File(...)):
    # Parse PDF
    with pdfplumber.open(file.file) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    values = extract_values(text)
    logger.info(f"Received blood test input: {values}")
    return values

# @app.get("/chat")
# async def chat_controller(prompt: str = "Inspire me"):
#     response = await async_client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": f"{system_prompt}"},
#             {"role": "user", "content": prompt},
#         ],
#     )
#     content = response.choices[0].message.content
#     return {"statement": content}

@app.post("/blood-results")
async def blood_results_controller(data: BloodTestResults):
    # Индекс системного иммунного воспаления
    logger.info(f"Received blood test input: {data}")
    print(data)

    sii = (data.neutrophils_absolute * data.platelets) / data.lymphocytes_absolute
    level, interpretation = interpret_sii(sii)
    return SIIResult(sii=round(sii, 2), level=level, interpretation=interpretation)
    # # Пример использования:
    # category = get_sii_category(SII)
    # logger.info(f"Категория: {category.emoji} {category.category}")
    # logger.info(f"Диапазон: {category.range_description}")
    # logger.info(f"Описание: {category.description}")
    # return {"SII": SII, "category": category}

# @app.post("/blood-results")
# async def blood_results_controller(results: BloodTestResults):
#     # Индекс системного иммунного воспаления
#     SII = results.neutrophils_absolute * results.platelets / results.white_blood_cells
#     system_prompt = ("You are doctor. User will provide Systemic Immune Inflammation Index - SII value. Based SII value"
#                      "return recommendation."
#                      "Following is the reseach info you can rely on before giving recommendations:"
#                      "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8519535/ Индекс системного иммунного воспаления является "
#                      "многообещающим неинвазивным биомаркером для прогнозирования выживаемости при раке мочевой системы:"
#                      "систематический обзор и метаанализ"
#                      "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9814343/ Прогностическая значимость индекса системного иммунного"
#                      "воспаления до лечения у пациентов с раком предстательной железы: метаанализ"
#                      "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9898902/ Прогностическое значение индекса системного иммунного"
#                      "воспаления до лечения у пациентов с раком предстательной железы: систематический обзор и метаанализ"
#                      "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7552553/ Прогностическое значение индекса системного иммунного"
#                      "воспаления у больных урологическими онкологическими заболеваниями: метаанализ"
#                      "https://www.europeanreview.org/article/24834 Прогностическое значение индекса системного иммунного воспаления у"
#                      "больных раком мочевой системы: метаанализ"
#                      "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6370019/"
#                      "Индекс системного иммунного воспаления является многообещающим неинвазивным маркером для"
#                      "прогнозирования выживаемости при раке легких: Метаанализ"
#                      "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8854201/"
#                      "Прогностическое значение индекса системного иммунного воспаления (SII) у больных мелкоклеточным раком"
#                      "легкого: метаанализ"
#                      "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9280894/"
#                      "Взаимосвязь между индексом системного иммунного воспаления и прогнозом у пациентов с немелкоклеточным"
#                      "раком легкого: метаанализ и систематический обзор"
#                      "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8436945/ Прогностическое и клинико-патологическое значение индекса"
#                      "системного иммунного воспаления при раке поджелудочной железы: метаанализ 2365 пациентов")

#     response = await async_client.chat.completions.create(
#         model="gpt-4.1-mini",
#         messages=[
#             {"role": "system", "content": f"{system_prompt}"},
#             {"role": "user", "content": str(SII)},
#         ],
#     )

#     return {"statement": response.choices[0].message.content}


# {
#   "hemoglobin": 138,
#   "white_blood_cells": 3.74,
#   "red_blood_cells": 4.57,
#   "platelets": 207,
#   "neutrophils_percent": 57.7,
#   "neutrophils_absolute": 2.16,
#   "lymphocytes_percent": 29.4,
#   "lymphocytes_absolute": 1.1,
#   "monocytes_percent": 11,
#   "monocytes_absolute": 0.41,
#   "eosinophils_percent": 1.6,
#   "eosinophils_absolute": 0.06,
#   "basophils_percent": 0.3,
#   "basophils_absolute": 0.01
# }