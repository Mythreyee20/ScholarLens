
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.schemas import ChatRequest, ChatResponse
from app.services.llm import LLMService

app = FastAPI(title="ScholarLens", version="0.1.0")

SettingsDep = Annotated[Settings, Depends(get_settings)]


@app.get("/health")
def health(settings: SettingsDep) -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        llm = LLMService()
        answer = llm.generate(request.message)
        return ChatResponse(response=answer)

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail="Both LLM providers failed.",
        ) from error


@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    llm = LLMService()

    return StreamingResponse(
        llm.stream_generate(request.message),
        media_type="text/plain",
    )


@app.get("/test-llm")
def test_llm():
    llm = LLMService()
    answer = llm.generate("Explain RAG in two sentences.")
    return {"response": answer}


@app.get("/usage")
def get_usage():
    return LLMService.get_usage()
