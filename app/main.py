from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from config import settings
from fastapi import FastAPI
from loguru import logger
from models.llm import llm_chain
from openai import AsyncOpenAI


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting up...")
    yield
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

async_client = AsyncOpenAI(api_key=settings.openai_api_key)
system_prompt = "You are a helpful assistant."


@app.get("/")
def read_root():
    return {"Key": settings.openai_api_key, 
            "Organization": settings.openai_organization}


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

@app.get("/generate/text")
def serve_language_model_controller(prompt: str) -> str:
    return llm_chain.invoke({"input": prompt})["text"]
