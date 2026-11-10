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


class RegisterRequest(BaseModel):
    client_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=8, max_length=100)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    client_name: str
    email: str
    role: str
