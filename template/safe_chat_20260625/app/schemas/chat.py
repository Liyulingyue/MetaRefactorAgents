from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class Message(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[Message]] = None

class ChatResponse(BaseModel):
    response: str
    history: List[Message]
