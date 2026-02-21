from pydantic import BaseModel
from typing import Optional


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
