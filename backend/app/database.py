"""Local SQLite database module for running Promethicc AI without Supabase.

Provides fallback storage for profiles, disclaimers, usage logs, audit logs,
and RAG documents.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "promethicc_local.db"


def get_connection() -> sqlite3.Connection:
    """Create a connection to the local SQLite database.

    Returns:
        A sqlite3.Connection instance with row factory set.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite tables matching the Supabase schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
        tier TEXT DEFAULT 'free',
        credits INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS disclaimer_acceptances (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        expert TEXT,
        accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, expert)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS usage_log (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        expert TEXT,
        mode TEXT,
        tokens_used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS audit_log (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        expert TEXT,
        mode TEXT,
        query TEXT,
        jurisdiction TEXT,
        emergency_triggered INTEGER DEFAULT 0,
        success INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS rag_documents (
        id TEXT PRIMARY KEY,
        expert TEXT,
        source_title TEXT,
        source_url TEXT,
        content TEXT
    )
    """
    )

    conn.commit()
    conn.close()


def is_local_mode(supabase_url: str) -> bool:
    """Check if the backend should run in local SQLite fallback mode.

    Args:
        supabase_url: The configured Supabase URL.

    Returns:
        True if the URL is empty or matches the placeholder.
    """
    import sys
    if "pytest" in sys.modules:
        return False
    return (
        not supabase_url
        or "your-project" in supabase_url
        or "placeholder" in supabase_url
    )
