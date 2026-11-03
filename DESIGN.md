# ScholarLens - System Design

## 1. Project Overview
ScholarLens is an AI-powered scholarship guideline assistant.
It aims to help students understand scholarship eligibility
and guidelines using Retrieval-Augmented Generation (RAG).

## 2. Current Architecture
- Backend: FastAPI
- Primary LLM: Gemini
- Fallback LLM: Groq
- Containerization: Docker
- Language: Python 3.12

## 3. API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /health | Check application health |
| GET | /test-llm | Test LLM response |
| GET | /usage | View token and cost usage |

## 4. LLM Fallback
Gemini is the primary provider.
Groq is used as a fallback when Gemini fails.

## 5. Usage Tracking
Tracks total requests, input tokens, output tokens,
total tokens, estimated cost, and last provider.
Usage data is currently stored in memory.

## 6. Database Design
No persistent database tables have been implemented yet.
PDF processing and vector database integration are planned.

## 7. Future Improvements
- Scholarship PDF ingestion
- Text extraction and chunking
- Vector database integration
- RAG-based question answering
- Student-facing interface