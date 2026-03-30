from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime


# ─── Chat ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Session ID for conversation memory",
    )
    stream: bool = Field(True, description="Stream response via SSE")


class SourceDocument(BaseModel):
    content: str = Field(..., description="Relevant chunk content")
    source: str = Field("unknown", description="Document source / filename")
    page: Optional[int] = Field(None, description="Page number if applicable")
    score: Optional[float] = Field(None, description="Relevance score")


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceDocument] = []
    session_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─── Sessions ────────────────────────────────────────────────────────────────

class SessionInfo(BaseModel):
    session_id: str
    title: str
    message_count: int
    created_at: str
    last_active: str


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]


# ─── Ingest ──────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    filename: str
    chunks_indexed: int
    message: str
