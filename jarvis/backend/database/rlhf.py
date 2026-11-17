"""RLHF (Reinforcement Learning from Human Feedback) Database & Storage Layer for JARVIS.

Manages feedback logs, user corrections, reward signals, and learned policy rules.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from jarvis.backend.database.db import get_db_connection

logger = logging.getLogger("JARVIS.RLHF.DB")


def init_rlhf_tables():
    """Ensure RLHF tables and indexes exist in SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Raw Feedback Logs (Every thumbs up, thumbs down, correction)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rlhf_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context_type TEXT NOT NULL,           -- 'chat_response', 'video_clip', 'viral_title', 'social_upload'
            prompt_or_input TEXT NOT NULL,
            action_or_output TEXT NOT NULL,
            feedback_type TEXT NOT NULL,          -- 'positive', 'negative', 'correction'
            reward_score REAL NOT NULL,           -- +1.0 (thumbs up), -1.0 (thumbs down), +2.0 (explicit correction)
            user_correction TEXT,                 -- what the user wanted instead
            learned_rule TEXT,                    -- distilled policy rule
            category TEXT DEFAULT 'general',     -- 'persona', 'video_editing', 'social_seo', 'general'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rlhf_feedback_type ON rlhf_feedback(feedback_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rlhf_category ON rlhf_feedback(category)")

    # 2. Consolidated Policy Rules (Weighted learned preferences)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rlhf_policy_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_text TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT 'general',
            reward_weight REAL DEFAULT 1.0,       -- cumulative reward signal from user
            confidence REAL DEFAULT 0.8,
            active BOOLEAN DEFAULT 1,
            times_applied INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rlhf_active ON rlhf_policy_rules(active)")

    # Seed foundational RLHF rules if table is newly initialized
    cursor.execute("SELECT COUNT(*) FROM rlhf_policy_rules")
    if cursor.fetchone()[0] == 0:
        foundational_rules = [
            ("Always use CUDA GPU acceleration for Whisper speech-to-text when available.", "performance", 5.0, 1.0),
            ("Ensure YouTube Shorts visibility is explicitly set to Public unless Boss asks for Unlisted.", "social_seo", 4.0, 0.95),
            ("Keep voice & chat responses crisp, confident, and 1 to 2 sentences (Iron Man style).", "persona", 4.5, 0.95),
            ("Maintain 45-minute to 60-minute anti-ban pacing between automated social uploads.", "social_seo", 5.0, 1.0),
            ("For gaming and high-energy video clips, use high-contrast animated subtitles.", "video_editing", 3.0, 0.85)
        ]
        for r_text, cat, rew, conf in foundational_rules:
            cursor.execute("""
                INSERT OR IGNORE INTO rlhf_policy_rules (rule_text, category, reward_weight, confidence)
                VALUES (?, ?, ?, ?)
            """, (r_text, cat, rew, conf))

    conn.commit()
    conn.close()


def save_feedback(
    context_type: str,
    prompt_or_input: str,
    action_or_output: str,
    feedback_type: str,
    reward_score: float,
    user_correction: Optional[str] = None,
    learned_rule: Optional[str] = None,
    category: str = "general"
) -> int:
    """Save raw feedback and reward score into SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rlhf_feedback (
            context_type, prompt_or_input, action_or_output, feedback_type,
            reward_score, user_correction, learned_rule, category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        context_type, prompt_or_input, action_or_output, feedback_type,
        reward_score, user_correction, learned_rule, category
    ))
    feedback_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return feedback_id


def upsert_policy_rule(rule_text: str, category: str, reward_delta: float) -> Dict[str, Any]:
    """Create or increment reward weight of a learned policy rule."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, reward_weight, active FROM rlhf_policy_rules WHERE rule_text = ?", (rule_text,))
    row = cursor.fetchone()

    if row:
        new_weight = row["reward_weight"] + reward_delta
        cursor.execute("""
            UPDATE rlhf_policy_rules
            SET reward_weight = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_weight, row["id"]))
        rule_id = row["id"]
    else:
        cursor.execute("""
            INSERT INTO rlhf_policy_rules (rule_text, category, reward_weight, confidence)
            VALUES (?, ?, ?, ?)
        """, (rule_text, category, max(1.0, reward_delta), 0.85))
        rule_id = cursor.lastrowid
        new_weight = reward_delta

    conn.commit()
    conn.close()

    return {"id": rule_id, "rule_text": rule_text, "reward_weight": new_weight}


def get_active_policy_rules(category: Optional[str] = None, min_weight: float = 0.0) -> List[Dict[str, Any]]:
    """Retrieve all active policy rules sorted by highest human reward weight."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT id, rule_text, category, reward_weight, confidence, times_applied, updated_at FROM rlhf_policy_rules WHERE active = 1 AND reward_weight >= ?"
    params: List[Any] = [min_weight]

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY reward_weight DESC, id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_feedback_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent feedback history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, context_type, prompt_or_input, action_or_output, feedback_type,
               reward_score, user_correction, learned_rule, category, created_at
        FROM rlhf_feedback
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_policy_rule(rule_id: int) -> bool:
    """Toggle a policy rule between active and inactive."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE rlhf_policy_rules SET active = 1 - active, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (rule_id,))
    conn.commit()
    conn.close()
    return True


def delete_policy_rule(rule_id: int) -> bool:
    """Delete a learned policy rule."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rlhf_policy_rules WHERE id = ?", (rule_id,))
    conn.commit()
    conn.close()
    return True


def get_rlhf_metrics() -> Dict[str, Any]:
    """Compute overall RLHF telemetry and reward statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM rlhf_feedback")
    total_feedback = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rlhf_feedback WHERE feedback_type = 'positive'")
    positive_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rlhf_feedback WHERE feedback_type = 'negative'")
    negative_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rlhf_feedback WHERE feedback_type = 'correction'")
    correction_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rlhf_policy_rules WHERE active = 1")
    active_rules_count = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(reward_score), 0) FROM rlhf_feedback")
    total_reward = cursor.fetchone()[0]

    conn.close()

    return {
        "total_feedback": total_feedback,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "correction_count": correction_count,
        "active_rules_count": active_rules_count,
        "total_cumulative_reward": round(total_reward, 1)
    }

