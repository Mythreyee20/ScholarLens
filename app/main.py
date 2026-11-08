from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.schemas import (
    AskRequest,
    AskResponse,
    ChatRequest,
    ChatResponse,
    Citation,
)
from app.services.llm import LLMService
from app.services.retriever import RetrieverService


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


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    # Step 1: Retrieve relevant PDF chunks
    try:
        retriever = RetrieverService()
        results = retriever.retrieve(request.question, limit=5)

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

    # Step 2: Build context from retrieved documents
    context_parts = []
    citations = []
    seen_citations = set()

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

        citation_key = (item["document"], item["page"])

        if citation_key not in seen_citations:
            citations.append(
                Citation(
                    document=item["document"],
                    page=item["page"],
                )
            )
            seen_citations.add(citation_key)

    context = "\n".join(context_parts)

    # Step 3: Ask the LLM using retrieved context
    prompt = f"""
You are ScholarLens, a scholarship guideline assistant.

Answer the user's question using ONLY the provided document context.

Rules:
1. Do not invent scholarship rules, eligibility criteria, dates or amounts.
2. If the context does not contain the answer, clearly say that the available documents do not provide enough information.
3. Keep the answer simple and clear.
4. Mention supporting source numbers such as [Source 1] when appropriate.
5. Do not invent document names or page numbers.

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

    # Step 4: Return answer and actual retrieved citations
    return AskResponse(
        answer=answer,
        citations=citations,
    )


@app.get("/test-llm")
def test_llm():
    llm = LLMService()
    answer = llm.generate("Explain RAG in two sentences.")
    return {"response": answer}


@app.get("/usage")
def get_usage():
    return LLMService.get_usage()