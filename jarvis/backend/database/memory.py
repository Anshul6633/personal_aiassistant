"""Long-Term Semantic & Conversational Memory System for JARVIS."""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from jarvis.backend.database.db import get_db_connection


class MemoryManager:
    def __init__(self):
        pass

    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Retrieve all active memories stored in SQLite."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, key, value, confidence, updated_at FROM memories ORDER BY category, key")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def set_memory(self, category: str, key: str, value: str, confidence: float = 1.0) -> bool:
        """Store or update a memory item."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memories (category, key, value, confidence, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                category=excluded.category,
                value=excluded.value,
                confidence=excluded.confidence,
                updated_at=CURRENT_TIMESTAMP
        """, (category, key, value, confidence))
        conn.commit()
        conn.close()
        return True

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory item by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        conn.close()
        return True

    def get_context_summary(self) -> str:
        """Format stored user preferences and context into a prompt injection string."""
        memories = self.get_all_memories()
        if not memories:
            return ""

        lines = ["--- USER PROFILE & MEMORY CONTEXT ---"]
        for m in memories:
            lines.append(f"- [{m['category'].upper()}] {m['key']}: {m['value']}")
        lines.append("--------------------------------------")
        return "\n".join(lines)

    def log_conversation(self, session_id: str, role: str, message: str, language: str = "en", audio_path: Optional[str] = None):
        """Append a dialogue turn to conversational history."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (session_id, role, message, language, audio_path)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, role, message, language, audio_path))
        conn.commit()
        conn.close()

    def get_recent_conversation(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve the last N dialogue turns for a session."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, message, language, timestamp
            FROM conversations
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (session_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in reversed(rows)]


memory_manager = MemoryManager()

