from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger
from openai import AsyncOpenAI

from src.middlewares import monitor_service
from src.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting up...")
    yield
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)
app.middleware("http")(monitor_service)

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

# @app.get("/generate/text")
# def generate_text_controller(prompt: str):
#     logger.info(f"Prompt: {prompt}")
#     print(settings.openai_key)
#     print(settings.openai_organization)
#     return llm_chain.run(prompt)
