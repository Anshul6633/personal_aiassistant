"""SQLite Database Initialization and Schema Management for JARVIS."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from jarvis.backend.config.settings import DB_PATH


def get_db_connection() -> sqlite3.Connection:
    """Create a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database tables, indexes, and initial default memory settings."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. User Memory & Preferences Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Conversation & Speech History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            audio_path TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Autonomous Tasks & Planning Engine Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            plan_json TEXT,
            status TEXT DEFAULT 'PENDING',
            progress INTEGER DEFAULT 0,
            result_summary TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Video & Content Clipping Pipeline Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clips (
            id TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            hook_strength REAL,
            story_completeness REAL,
            info_value REAL,
            engagement_potential REAL,
            audio_quality REAL,
            visual_quality REAL,
            total_score REAL,
            start_time REAL,
            end_time REAL,
            duration REAL,
            output_path TEXT,
            thumbnail_path TEXT,
            subtitles_path TEXT,
            tags TEXT,
            caption TEXT,
            status TEXT DEFAULT 'DISCOVERED',
            published_youtube BOOLEAN DEFAULT 0,
            published_instagram BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. Connected Social Accounts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_accounts (
            platform TEXT PRIMARY KEY,
            account_id TEXT,
            account_name TEXT,
            channel_url TEXT,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry TIMESTAMP,
            status TEXT DEFAULT 'DISCONNECTED',
            last_synced TIMESTAMP
        )
    """)

    # 6. Audit & Safety Event Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT NOT NULL,
            user_approved BOOLEAN DEFAULT 1,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 7. Video Studio Projects Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studio_projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            aspect_ratio TEXT DEFAULT '16:9',
            width INTEGER DEFAULT 1920,
            height INTEGER DEFAULT 1080,
            fps INTEGER DEFAULT 30,
            duration REAL DEFAULT 60.0,
            timeline_json TEXT NOT NULL,
            thumbnail_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 8. YouTube Scheduled Auto-Publishing Queue
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS youtube_schedule_queue (
            id TEXT PRIMARY KEY,
            drive_file_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            tags TEXT,
            scheduled_time TEXT NOT NULL,
            privacy TEXT DEFAULT 'public',
            status TEXT DEFAULT 'QUEUED',
            youtube_url TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_yt_queue_status ON youtube_schedule_queue(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_yt_queue_scheduled ON youtube_schedule_queue(scheduled_time)")

    # 9. Instagram Scheduled Auto-Publishing Queue
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instagram_schedule_queue (
            id TEXT PRIMARY KEY,
            video_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            caption TEXT NOT NULL,
            tags TEXT,
            scheduled_time TEXT NOT NULL,
            privacy TEXT DEFAULT 'public',
            status TEXT DEFAULT 'QUEUED',
            post_url TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ig_queue_status ON instagram_schedule_queue(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ig_queue_scheduled ON instagram_schedule_queue(scheduled_time)")

    conn.commit()

    # Seed initial user preferences if empty
    cursor.execute("SELECT COUNT(*) FROM memories")
    if cursor.fetchone()[0] == 0:
        default_memories = [
            ("personality", "assistant_name", "JARVIS"),
            ("personality", "creator_name", "Boss"),
            ("personality", "tone", "Avengers Iron Man style - witty, confident, proactive"),
            ("content", "primary_niche", "Tech, Motivation, AI, Entertainment Podcasts"),
            ("content", "daily_target_clips", "30"),
            ("content", "default_aspect_ratio", "9:16"),
            ("system", "autonomy_mode", "SUPERVISED")
        ]
        for cat, k, v in default_memories:
            cursor.execute(
                "INSERT OR REPLACE INTO memories (category, key, value) VALUES (?, ?, ?)",
                (cat, k, v)
            )
        conn.commit()

    conn.close()


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully at:", DB_PATH)

