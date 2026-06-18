"""Disclaimer management for high-stakes experts (Med, Law).

Users must accept a per-expert disclaimer before their first query.
The backend enforces this — it is not just a frontend modal.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Disclaimer texts — one per high-stakes expert
# ---------------------------------------------------------------------------

DISCLAIMERS: dict[str, str] = {
    "med": (
        "This service provides general health information only. It is NOT "
        "a substitute for professional medical advice, diagnosis, or treatment. "
        "Always seek the advice of a licensed physician or other qualified health "
        "provider with any questions you may have regarding a medical condition. "
        "Never disregard professional medical advice or delay in seeking it "
        "because of something you read here."
    ),
    "law": (
        "This service provides general legal information only. It is NOT "
        "legal advice and does NOT create an attorney-client relationship. "
        "Laws vary by jurisdiction and change over time. For advice specific "
        "to your situation, consult a licensed attorney in your jurisdiction."
    ),
}


# ---------------------------------------------------------------------------
# Supabase REST helpers (httpx-based, service-role key)
# ---------------------------------------------------------------------------

def _headers() -> dict[str, str]:
    """Build standard Supabase REST API headers.

    Returns:
        Dict of HTTP headers including apikey and Authorization.
    """
    return {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


async def check_disclaimer_accepted(
    client: httpx.AsyncClient,
    user_id: str,
    expert: str,
) -> bool:
    """Check whether a user has previously accepted the disclaimer for an expert.

    Args:
        client: An httpx.AsyncClient instance.
        user_id: Supabase auth user UUID.
        expert: Expert slug (e.g. 'med', 'law').

    Returns:
        True if a matching acceptance row exists, False otherwise.
    """
    from app.database import is_local_mode, get_connection
    if is_local_mode(settings.SUPABASE_URL):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM disclaimer_acceptances WHERE user_id = ? AND expert = ?",
            (user_id, expert)
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None

    url = (
        f"{settings.SUPABASE_URL}/rest/v1/disclaimer_acceptances"
        f"?user_id=eq.{user_id}&expert=eq.{expert}&select=id"
    )
    resp = await client.get(url, headers=_headers())
    resp.raise_for_status()
    rows: list[dict] = resp.json()
    return len(rows) > 0


async def accept_disclaimer(
    client: httpx.AsyncClient,
    user_id: str,
    expert: str,
) -> None:
    """Record a user's acceptance of a high-stakes expert disclaimer.

    Args:
        client: An httpx.AsyncClient instance.
        user_id: Supabase auth user UUID.
        expert: Expert slug (e.g. 'med', 'law').
    """
    from app.database import is_local_mode, get_connection
    if is_local_mode(settings.SUPABASE_URL):
        import uuid
        import sqlite3
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO disclaimer_acceptances (id, user_id, expert) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), user_id, expert)
            )
            conn.commit()
            logger.info("Disclaimer accepted (SQLite): user=%s expert=%s", user_id, expert)
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
        return

    url = f"{settings.SUPABASE_URL}/rest/v1/disclaimer_acceptances"
    payload = {
        "user_id": user_id,
        "expert": expert,
        "accepted_at": datetime.now(timezone.utc).isoformat(),
    }
    resp = await client.post(url, headers=_headers(), json=payload)
    resp.raise_for_status()
    logger.info("Disclaimer accepted: user=%s expert=%s", user_id, expert)
