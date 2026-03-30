"""
Session-based conversation memory backed by SQLite.
Each session stores its chat history independently.
"""
import json
import asyncio
from datetime import datetime
from typing import Optional

import aiosqlite
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

DB_PATH = "./data/sessions.db"


async def init_db() -> None:
    """Initialize the SQLite database schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                title      TEXT NOT NULL DEFAULT 'New Chat',
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
            """
        )
        await db.commit()


async def ensure_session(session_id: str, first_message: Optional[str] = None) -> None:
    """Create a session if it doesn't exist."""
    now = datetime.utcnow().isoformat()
    title = (first_message[:50] + "…") if first_message and len(first_message) > 50 else (first_message or "New Chat")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO sessions (session_id, title, created_at, last_active)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, title, now, now),
        )
        await db.execute(
            "UPDATE sessions SET last_active = ? WHERE session_id = ?",
            (now, session_id),
        )
        await db.commit()


async def add_message(session_id: str, role: str, content: str) -> None:
    """Append a message to a session's history."""
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        await db.execute(
            "UPDATE sessions SET last_active = ? WHERE session_id = ?",
            (now, session_id),
        )
        await db.commit()


async def get_history(session_id: str, limit: int = 20) -> list[BaseMessage]:
    """Retrieve the last `limit` messages for LangChain context."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT role, content FROM messages
            WHERE session_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (session_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()

    messages: list[BaseMessage] = []
    for role, content in reversed(rows):
        if role == "human":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages


async def list_sessions() -> list[dict]:
    """List all sessions with metadata."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT s.session_id, s.title, s.created_at, s.last_active,
                   COUNT(m.id) as message_count
            FROM sessions s
            LEFT JOIN messages m ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.last_active DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()

    return [
        {
            "session_id": row[0],
            "title": row[1],
            "created_at": row[2],
            "last_active": row[3],
            "message_count": row[4],
        }
        for row in rows
    ]


async def delete_session(session_id: str) -> bool:
    """Delete a session and all its messages."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM sessions WHERE session_id = ?", (session_id,)
        )
        await db.execute(
            "DELETE FROM messages WHERE session_id = ?", (session_id,)
        )
        await db.commit()
        return cursor.rowcount > 0
