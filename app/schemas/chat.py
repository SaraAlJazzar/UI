from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ImageInfo(BaseModel):
    path: str
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime


class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: str
    text: str
    updated_at: Optional[datetime] = None
    images: Optional[List[ImageInfo]] = []


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
