from typing import Annotated

from fastapi import Depends, FastAPI

from app.config import Settings, get_settings
from app.services.llm import LLMService

app = FastAPI(title="ScholarLens", version="0.1.0")

SettingsDep = Annotated[Settings, Depends(get_settings)]


@app.get("/health")
def health(settings: SettingsDep) -> dict:
    """Liveness: the process is up. Must be fast and must not call the LLM or the DB."""
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}

@app.get("/test-llm")
def test_llm():
    llm = LLMService()
    answer = llm.generate("Explain RAG in two sentences.")
    return {"response": answer}

@app.get("/usage")
def get_usage():
    return LLMService.get_usage()




