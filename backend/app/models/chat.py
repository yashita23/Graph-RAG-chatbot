from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    answer: str
    retrieved_nodes: list[dict] = []
    relationships: list[dict] = []
    session_id: str