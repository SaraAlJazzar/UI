from pydantic import BaseModel, Field
from typing import Optional, List


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
