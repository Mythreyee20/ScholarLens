
import os
import re
from pathlib import Path
from uuid import uuid4
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    UploadFile,
    File,
)
from fastapi.responses import StreamingResponse
from redis import Redis
from rq import Queue, Retry

from app.config import Settings, get_settings
from app.schemas import (
    AskRequest,
    AskResponse,
    ChatRequest,
    ChatResponse,
    Citation,
    RegisterRequest,
    LoginRequest,
)
from app.services.auth import (
    init_auth_db,
    register_client,
    authenticate_client,
    create_access_token,
    get_current_user,
)
from app.services.ingestion import (
    ingest_all_pdfs,
    ingest_client_pdfs,
)
from app.services.llm import LLMService
from app.services.retriever import RetrieverService


app = FastAPI(title="ScholarLens", version="0.1.0")

SettingsDep = Annotated[Settings, Depends(get_settings)]


# Initialize authentication database
@app.on_event("startup")
def setup_auth_database():
    init_auth_db()


# Register a new client
@app.post("/register")
def register(request: RegisterRequest):
    user = register_client(
        request.client_name,
        request.email,
        request.password,
    )

    return {
        "message": "Registration successful",
        "user": user,
    }


# Client login
@app.post("/login")
def login(request: LoginRequest):
    user = authenticate_client(
        request.email,
        request.password,
    )

    token = create_access_token(user["id"])

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# Get logged-in client profile
@app.get("/me")
def get_profile(user: dict = Depends(get_current_user)):
    return user


# Health check
@app.get("/health")
def health(settings: SettingsDep) -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


# Chat endpoint
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


# Streaming chat endpoint
@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    llm = LLMService()

    return StreamingResponse(
        llm.stream_generate(request.message),
        media_type="text/plain",
    )


# Authenticated scholarship question endpoint
@app.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    user: dict = Depends(get_current_user),
):
    try:
        retriever = RetrieverService()

        results = retriever.retrieve(
            request.question,
            limit=5,
            client_id=user["id"],
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    if not results:
        return AskResponse(
            answer="I could not find relevant information in the available scholarship documents.",
            citations=[],
        )

    context_parts = []

    for index, item in enumerate(results, start=1):
        context_parts.append(
            f"""
[Source {index}]
Document: {item['document']}
Page: {item['page']}
Headings: {', '.join(item['headings'])}
Content:
{item['chunk_text']}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are ScholarLens, a scholarship guideline assistant.

Answer using ONLY the provided document context.

Rules:
1. Never invent scholarship rules, dates, amounts or eligibility criteria.
2. Use only sources that directly support your answer.
3. Cite supporting sources using their exact labels, such as [Source 1].
4. Never cite a source that does not support the claim.
5. If information is insufficient, clearly say so.
6. Keep the answer simple and clear.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{request.question}

ANSWER:
"""

    try:
        llm = LLMService()
        answer = llm.generate(prompt)

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail="Both LLM providers failed.",
        ) from error

    # Keep only citations referenced in the answer
    source_numbers = {
        int(number)
        for number in re.findall(
            r"\[Source\s+(\d+)\]",
            answer,
            re.IGNORECASE,
        )
    }

    citations = []
    seen_citations = set()

    for index, item in enumerate(results, start=1):
        if index not in source_numbers:
            continue

        citation_key = (item["document"], item["page"])

        if citation_key not in seen_citations:
            citations.append(
                Citation(
                    document=item["document"],
                    page=item["page"],
                )
            )
            seen_citations.add(citation_key)

    return AskResponse(
        answer=answer,
        citations=citations,
    )


# Client-specific PDF upload
@app.post("/upload-pdf")
def upload_pdf(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    # Verify PDF signature
    header = file.file.read(5)
    file.file.seek(0)

    if header != b"%PDF-":
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file.",
        )

    client_id = user["id"]

    upload_dir = Path(
        f"/app/data/client_uploads/{client_id}"
    )
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{uuid4().hex}.pdf"

    max_size = 20 * 1024 * 1024
    total_size = 0

    try:
        with open(file_path, "wb") as output:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail="PDF must be smaller than 20 MB.",
                    )

                output.write(chunk)

        redis_conn = Redis.from_url(
            os.getenv(
                "REDIS_URL",
                "redis://localhost:6379/0",
            )
        )

        queue = Queue(
            "ingestion",
            connection=redis_conn,
        )

        job = queue.enqueue(
            ingest_client_pdfs,
            str(upload_dir),
            client_id,
            retry=Retry(
                max=3,
                interval=[10, 30, 60],
            ),
        )

        return {
            "message": "PDF uploaded and ingestion queued.",
            "client_id": client_id,
            "job_id": job.id,
        }

    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise

    except Exception as error:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=503,
            detail=f"PDF upload failed: {error}",
        ) from error

    finally:
        file.file.close()


# Test LLM
@app.get("/test-llm")
def test_llm():
    llm = LLMService()
    answer = llm.generate(
        "Explain RAG in two sentences."
    )

    return {"response": answer}


# LLM usage statistics
@app.get("/usage")
def get_usage():
    return LLMService.get_usage()


# Queue shared PDF ingestion
@app.post("/ingest")
def start_ingestion():
    try:
        redis_conn = Redis.from_url(
            os.getenv(
                "REDIS_URL",
                "redis://localhost:6379/0",
            )
        )

        queue = Queue(
            "ingestion",
            connection=redis_conn,
        )

        job = queue.enqueue(
            ingest_all_pdfs,
            retry=Retry(
                max=3,
                interval=[10, 30, 60],
            ),
        )

        return {
            "message": "Ingestion queued",
            "job_id": job.id,
        }

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Could not queue ingestion: {error}",
        ) from error
