from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile
from loguru import logger
from openai import AsyncOpenAI
import ast
from datetime import datetime
from src.middlewares import monitor_service
from src.models.llm import system_prompt
from src.schemas.blood_results import BloodTestResults, blood_test_names
from src.services.ocr_aws import analyze_document
from src.settings import settings
from typing import Dict
import fitz  # PyMuPDF
import re
from fastapi.responses import JSONResponse
import pdfplumber
from rapidfuzz import process
from typing import Optional, Tuple
from mangum import Mangum


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting up...")
    yield
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)
# Allow your frontend origin (e.g., http://localhost:3000)
origins = [
    "http://localhost:3000",
    "*.lovable.app",
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
    return {"Fact": "Dimash, you are doing great. Just imagine what you can achieve, if you continue putting effort"
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
    "Гемоглобин": r"Гемоглобин\s+[A-Z]*\s*([\d.,]+)",
    "Лейкоциты": r"Лейкоциты\s+[A-Z]*\s*([\d.,]+)",
    "Эритроциты": r"Эритроциты\s+[A-Z]*\s*([\d.,]+)",
    "Тромбоциты": r"Тромбоциты\s+[A-Z]*\s*([\d.,]+)",
    "Нейтрофилы %": r"Нейтрофилы\s*NEU%\s*([\d.,]+)",
    "Нейтрофилы #": r"Нейтрофилы\s*\(абс. кол-во\)\s*NEU#\s*([\d.,]+)",
    "Лимфоциты %": r"Лимфоциты\s*LYM%\s*([\d.,]+)",
    "Лимфоциты #": r"Лимфоциты\s*\(абс. кол-во\)\s*LYM#\s*([\d.,]+)",
    "Моноциты %": r"Моноциты\s*MON%\s*([\d.,]+)",
    "Моноциты #": r"Моноциты\s*\(абс. кол-во\)\s*MON#\s*([\d.,]+)",
    "Эозинофилы %": r"Эозинофилы\s*EOS%\s*([\d.,]+)",
    "Эозинофилы #": r"Эозинофилы\s*\(абс. кол-во\)\s*EOS#\s*([\d.,]+)",
    "Базофилы %": r"Базофилы\s*BAS%\s*([\d.,]+)",
    "Базофилы #": r"Базофилы\s*\(абс. кол-во\)\s*BAS#\s*([\d.,]+)",
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
    return values

@app.get("/chat")
async def chat_controller(prompt: str = "Inspire me"):
    response = await async_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content
    return {"statement": content}

@app.post("/blood-results")
async def blood_results_controller(results: BloodTestResults):
    # Индекс системного иммунного воспаления
    SII = results.neutrophils_absolute * results.platelets / results.white_blood_cells
    system_prompt = ("You are doctor. User will provide Systemic Immune Inflammation Index - SII value. Based SII value"
                     "return recommendation."
                     "Following is the reseach info you can rely on before giving recommendations:"
                     "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8519535/ Индекс системного иммунного воспаления является "
                     "многообещающим неинвазивным биомаркером для прогнозирования выживаемости при раке мочевой системы:"
                     "систематический обзор и метаанализ"
                     "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9814343/ Прогностическая значимость индекса системного иммунного"
                     "воспаления до лечения у пациентов с раком предстательной железы: метаанализ"
                     "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9898902/ Прогностическое значение индекса системного иммунного"
                     "воспаления до лечения у пациентов с раком предстательной железы: систематический обзор и метаанализ"
                     "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7552553/ Прогностическое значение индекса системного иммунного"
                     "воспаления у больных урологическими онкологическими заболеваниями: метаанализ"
                     "https://www.europeanreview.org/article/24834 Прогностическое значение индекса системного иммунного воспаления у"
                     "больных раком мочевой системы: метаанализ"
                     "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6370019/"
                     "Индекс системного иммунного воспаления является многообещающим неинвазивным маркером для"
                     "прогнозирования выживаемости при раке легких: Метаанализ"
                     "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8854201/"
                     "Прогностическое значение индекса системного иммунного воспаления (SII) у больных мелкоклеточным раком"
                     "легкого: метаанализ"
                     "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9280894/"
                     "Взаимосвязь между индексом системного иммунного воспаления и прогнозом у пациентов с немелкоклеточным"
                     "раком легкого: метаанализ и систематический обзор"
                     "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8436945/ Прогностическое и клинико-патологическое значение индекса"
                     "системного иммунного воспаления при раке поджелудочной железы: метаанализ 2365 пациентов")

    response = await async_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": str(SII)},
        ],
    )

    return {"statement": response.choices[0].message.content}

@app.post("/analyze")
async def analyze_endpoint(file: UploadFile = File(...)):
    contents = await file.read()
    result = await analyze_document(contents)
    system_prompt = (f"You are a doctor. You will be given blood test results. "
                     f"Your task is to find out 14 values for the: Гемоглобин, Лейкоциты, Эритроциты, Тромбоциты, "
                     f"Нейтрофилы %, Нейтрофилы #, Лимфоциты %, Лимфоциты #, Моноциты %, Моноциты #, Эозинофилы %, "
                     f"Эозинофилы #, Базофилы %, Базофилы #")

    response = await async_client.beta.chat.completions.parse(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": [result]},
        ],
        response_format=BloodTestResults
    )
    message = response.choices[0].message
    return message.parsed if message.parsed is not None else message.refusal

    # content = response.choices[0].message.content
    #
    # return content


# @app.get("/generate/text")
# def generate_text_controller(prompt: str):
#     logger.info(f"Prompt: {prompt}")
#     print(settings.openai_key)
#     print(settings.openai_organization)
#     return llm_chain.run(prompt)
