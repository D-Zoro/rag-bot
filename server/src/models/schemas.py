#pydantic schemas lol

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    message: str
    session_id: str
    user_id: Optional[str] = "default_user"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[Dict[str, Any]]
    timestamp: datetime

class DocumentInfo(BaseModel):
    filename: str
    doc_type: str
    chunk_count: int
    upload_time: datetime

