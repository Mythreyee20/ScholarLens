from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    response: str


class AskRequest(BaseModel):
    question: str = Field(min_length=3)


class Citation(BaseModel):
    document: str
    page: int


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]