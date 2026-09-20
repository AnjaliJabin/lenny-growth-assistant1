from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


class SessionCreate(BaseModel):
    title: str = "New Chat"
    user_metadata: dict = Field(default_factory=dict)


class SessionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    session_id: str
    role: str
    content: str
    sources: list[dict] = []
    artifact: dict | None = None
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    message: MessageResponse
    provider: str


class ArtifactRequest(BaseModel):
    session_id: str
    type: str = Field(..., pattern="^(markdown|html)$")
    topic: str = Field(..., min_length=1, max_length=500)


class Ship30Request(BaseModel):
    session_id: str
    topic: str = Field(..., min_length=1, max_length=500)


class HealthResponse(BaseModel):
    status: str
    provider: str
    db: str
    retrieval: str
