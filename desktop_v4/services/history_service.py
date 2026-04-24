"""SQLite-backed local history for desktop chat sessions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import List, Optional
import uuid


DB_PATH = Path(__file__).resolve().parents[1] / "desktop_history.db"


@dataclass
class SessionRecord:
    session_id: str
    title: str
    created_at: str
    updated_at: str


@dataclass
class MessageRecord:
    id: int
    role: str
    content: str
    sql_query: str
    answer: str
    explanation: str
    insight: str
    intent: str
    created_at: str


class HistoryService:
    def __init__(self) -> None:
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(DB_PATH)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sql_query TEXT DEFAULT '',
                    answer TEXT DEFAULT '',
                    explanation TEXT DEFAULT '',
                    insight TEXT DEFAULT '',
                    intent TEXT DEFAULT 'general_query',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS query_cache (
                    cache_key TEXT PRIMARY KEY,
                    answer TEXT NOT NULL,
                    sql_query TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    insight TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    warnings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_session(self, title: str = "New chat") -> str:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions(session_id, title, created_at, updated_at) VALUES(?, ?, ?, ?)",
                (session_id, title, now, now),
            )
            conn.commit()
        return session_id

    def list_sessions(self) -> List[SessionRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT session_id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        return [SessionRecord(*row) for row in rows]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sql_query: str = "",
        answer: str = "",
        explanation: str = "",
        insight: str = "",
        intent: str = "general_query",
    ) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages(session_id, role, content, sql_query, answer, explanation, insight, intent, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, role, content, sql_query, answer, explanation, insight, intent, now),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
            conn.commit()

    def update_title(self, session_id: str, title: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE session_id = ?",
                (title, datetime.utcnow().isoformat(), session_id),
            )
            conn.commit()

    def get_messages(self, session_id: str) -> List[MessageRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, role, content, sql_query, answer, explanation, insight, intent, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()
        return [MessageRecord(*row) for row in rows]

    def update_user_message(self, session_id: str, message_id: int, content: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE messages
                SET content = ?, created_at = ?
                WHERE id = ? AND session_id = ? AND role = 'user'
                """,
                (content, now, message_id, session_id),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
            conn.commit()

    def truncate_after_message(self, session_id: str, message_id: int) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM messages WHERE session_id = ? AND id > ?",
                (session_id, message_id),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
            conn.commit()

    def update_assistant_message(
        self,
        session_id: str,
        message_id: int,
        sql_query: str,
        answer: str,
        explanation: str,
        insight: str,
        intent: str,
    ) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE messages
                SET content = '',
                    sql_query = ?,
                    answer = ?,
                    explanation = ?,
                    insight = ?,
                    intent = ?,
                    created_at = ?
                WHERE id = ? AND session_id = ? AND role = 'assistant'
                """,
                (sql_query, answer, explanation, insight, intent, now, message_id, session_id),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
            conn.commit()

    def get_previous_user_message(
        self,
        session_id: str,
        before_message_id: int,
    ) -> Optional[MessageRecord]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, role, content, sql_query, answer, explanation, insight, intent, created_at
                FROM messages
                WHERE session_id = ? AND role = 'user' AND id < ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id, before_message_id),
            ).fetchone()
        return MessageRecord(*row) if row else None

    def delete_session(self, session_id: str) -> None:
        """Delete a chat session and all its messages."""
        with self._connect() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()

    def ensure_default_session(self) -> str:
        sessions = self.list_sessions()
        if sessions:
            return sessions[0].session_id
        return self.create_session("New chat")

    def create_startup_session(self) -> str:
        """Always start app with a fresh chat while keeping prior chats accessible."""
        timestamp = datetime.utcnow().strftime("%H:%M")
        return self.create_session(f"New chat ({timestamp})")

    def latest_user_prompt(self, session_id: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT content
                FROM messages
                WHERE session_id = ? AND role = 'user'
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        return row[0] if row else None

    def get_cached_response(self, cache_key: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT answer, sql_query, explanation, insight, intent, warnings_json
                FROM query_cache
                WHERE cache_key = ?
                """,
                (cache_key,),
            ).fetchone()
            if not row:
                return None
            conn.execute(
                "UPDATE query_cache SET last_used_at = ? WHERE cache_key = ?",
                (datetime.utcnow().isoformat(), cache_key),
            )
            conn.commit()
        return {
            "answer": row[0],
            "sql_query": row[1],
            "explanation": row[2],
            "insight": row[3],
            "intent": row[4],
            "warnings": json.loads(row[5]) if row[5] else [],
        }

    def set_cached_response(
        self,
        cache_key: str,
        answer: str,
        sql_query: str,
        explanation: str,
        insight: str,
        intent: str,
        warnings: list[str],
    ) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO query_cache(
                    cache_key, answer, sql_query, explanation, insight, intent,
                    warnings_json, created_at, last_used_at
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    answer = excluded.answer,
                    sql_query = excluded.sql_query,
                    explanation = excluded.explanation,
                    insight = excluded.insight,
                    intent = excluded.intent,
                    warnings_json = excluded.warnings_json,
                    last_used_at = excluded.last_used_at
                """,
                (
                    cache_key,
                    answer,
                    sql_query,
                    explanation,
                    insight,
                    intent,
                    json.dumps(warnings or []),
                    now,
                    now,
                ),
            )
            conn.commit()

