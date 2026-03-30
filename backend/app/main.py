"""
FastAPI application entrypoint.
Provides endpoints for chat (streaming + non-streaming),
document ingestion, and session management.
"""
import os
import shutil
import asyncio
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.schemas import (
    ChatRequest,
    ChatResponse,
    IngestResponse,
    SessionListResponse,
    SessionInfo,
)
from app.memory import init_db, list_sessions, delete_session
from app.ingest import ingest_file
from app import agent as rag_agent

# ── App setup ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="RAG Chatbot API",
    version="1.0.0",
    description="Local RAG chatbot powered by Google Gemini & Pinecone",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.upload_dir, exist_ok=True)


@app.on_event("startup")
async def startup():
    await init_db()


# ── Health ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ── Chat ──────────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Chat with the RAG agent.
    If `stream=true`, returns SSE stream. Otherwise returns JSON.
    """
    if req.stream:
        async def event_generator():
            try:
                async for token in rag_agent.chat_stream(req.message, req.session_id):
                    if token.startswith("\n\n__SOURCES__"):
                        # Send sources as a typed event
                        sources_json = token.replace("\n\n__SOURCES__", "")
                        yield {
                            "event": "sources",
                            "data": sources_json,
                        }
                    else:
                        yield {
                            "event": "token",
                            "data": token,
                        }
            except Exception as e:
                yield {"event": "error", "data": str(e)}
            finally:
                yield {"event": "done", "data": ""}

        return EventSourceResponse(event_generator())
    else:
        answer, sources = await rag_agent.chat(req.message, req.session_id)
        return ChatResponse(
            answer=answer,
            sources=sources,
            session_id=req.session_id,
        )


# ── Ingest ────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(file: UploadFile = File(...)):
    """Upload and index a document into Pinecone."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {ALLOWED_EXTENSIONS}",
        )

    save_path = os.path.join(settings.upload_dir, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        chunks = await ingest_file(save_path, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return IngestResponse(
        filename=file.filename,
        chunks_indexed=chunks,
        message=f"Successfully indexed {chunks} chunks from '{file.filename}'",
    )


# ── Sessions ──────────────────────────────────────────────────────────────

@app.get("/sessions", response_model=SessionListResponse)
async def get_sessions():
    """List all conversation sessions."""
    rows = await list_sessions()
    sessions = [
        SessionInfo(
            session_id=r["session_id"],
            title=r["title"],
            message_count=r["message_count"],
            created_at=r["created_at"],
            last_active=r["last_active"],
        )
        for r in rows
    ]
    return SessionListResponse(sessions=sessions)


@app.delete("/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    """Delete a session and its message history."""
    deleted = await delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": f"Session '{session_id}' deleted"}
