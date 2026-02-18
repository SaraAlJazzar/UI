from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Chat schemas
class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: str
    text: str
    updated_at: Optional[datetime] = None


class MessageUpdate(BaseModel):
    text: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    language: Optional[str] = None
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    message: str
    response: str
    session_id: str


# Chat session schemas
class SessionSummary(BaseModel):
    session_id: str
    title: str
    updated_at: datetime


class SessionDetail(BaseModel):
    session_id: str
    title: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime


# RAG schemas
class RAGRequest(BaseModel):
    query: str
    num_links: int = Field(default=1, ge=1, le=10, description="Number of links to retrieve and send to the model")
    website: str = Field(default="altibbi", description="Website to search: altibbi, mayoclinic, or mawdoo3")
    api_key: Optional[str] = None
    model: Optional[str] = None


class LinkInfo(BaseModel):
    url: str
    title: str
    snippet: str


class RAGResponse(BaseModel):
    query: str
    source: str
    response: str
    used_links: List[LinkInfo] = []


# Settings schemas
class SettingsUpdate(BaseModel):
    api_key: Optional[str] = ""
    model: Optional[str] = "gemini-2.5-flash-lite"
    language: Optional[str] = "ar"
    context_messages: Optional[int] = 4


class SettingsResponse(BaseModel):
    api_key: str
    model: str
    language: str
    context_messages: int

    class Config:
        from_attributes = True