import ast
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Optional, Tuple

import fitz  # PyMuPDF
import pdfplumber
from fastapi import FastAPI, File, HTTPException, UploadFile
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
from src.services.helper import (
    convert_lab_results,
    extract_text_fitz,
    extract_text_pdfplumber,
    interpret_sii,
    parse_results,
)
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
    "https://oncotest.kz",
    "http://medtech-backend-alb-988383858.us-east-1.elb.amazonaws.com",
    "https://medtech-backend-alb-988383858.us-east-1.elb.amazonaws.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Используем список разрешенных доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(monitor_service)

async_client = AsyncOpenAI(api_key=settings.openai_api_key)

handler = Mangum(app)

@app.get("/")
def read_root():
    return {"Fact": "Dimash, you are doing great. Just imagine what you can achieve, if you continue putting effort "
                     "every day for the next 30 years"}

@app.post("/upload-bloodtest/", response_model=BloodTestResults)
async def upload_bloodtest(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported")

    pdf_bytes = await file.read()

    # Try to extract with pdfplumber first
    text = extract_text_pdfplumber(pdf_bytes).strip()

    # If extraction fails or too short, try fitz as fallback
    if len(text) < 100:
        text = extract_text_fitz(pdf_bytes)

    # Optional: raise error if still no text
    if len(text.strip()) < 30:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF.")

    results = parse_results(text)
    return results

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
    
    try:
        # Проверяем наличие необходимых значений
        if data.neutrophils_absolute is None or data.platelets is None or data.lymphocytes_absolute is None:
            raise ValueError("Отсутствуют необходимые значения для расчета SII")
            
        if data.lymphocytes_absolute == 0:
            raise ValueError("Значение лимфоцитов (абс.) не может быть нулевым")
            
        sii = (data.neutrophils_absolute * data.platelets) / data.lymphocytes_absolute
        level, interpretation = interpret_sii(sii)
        return SIIResult(sii=round(sii, 2), level=level, interpretation=interpretation)
    except Exception as e:
        logger.error(f"Error in blood_results_controller: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

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