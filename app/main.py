import os

from dotenv import load_dotenv
from fastapi import FastAPI
from openai import AsyncOpenAI

load_dotenv()

app = FastAPI()

openai_api_key = os.getenv("OPENAI_API_KEY")
async_client = AsyncOpenAI(api_key=openai_api_key)
system_prompt = "You are a helpful assistant."


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

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

