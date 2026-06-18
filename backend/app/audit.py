"""Audit logging and rate-limit enforcement via Supabase REST API.

Every interaction is recorded (GEMINI.md rule 8). Rate limiting is
enforced server-side (rule 7) to protect the shared CPU resource.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


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


async def log_usage(
    client: httpx.AsyncClient,
    user_id: str,
    expert: str,
    mode: str,
    tokens_used: int,
) -> None:
    """Insert a row into the usage_log table.

    Args:
        client: An httpx.AsyncClient instance.
        user_id: Supabase auth user UUID.
        expert: Expert slug used.
        mode: 'offline' or 'online'.
        tokens_used: Number of tokens consumed.
    """
    from app.database import is_local_mode, get_connection
    if is_local_mode(settings.SUPABASE_URL):
        import uuid
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usage_log (id, user_id, expert, mode, tokens_used) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), user_id, expert, mode, tokens_used)
            )
            conn.commit()
        except Exception as exc:
            logger.error("Failed to write SQLite usage_log: %s", exc)
        finally:
            conn.close()
        return

    url = f"{settings.SUPABASE_URL}/rest/v1/usage_log"
    payload = {
        "user_id": user_id,
        "expert": expert,
        "mode": mode,
        "tokens_used": tokens_used,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        resp = await client.post(url, headers=_headers(), json=payload)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Failed to write usage_log: %s", exc)


async def log_audit(
    client: httpx.AsyncClient,
    user_id: str,
    expert: str,
    mode: str,
    query: str,
    jurisdiction: str | None,
    emergency_triggered: bool,
    success: bool,
) -> None:
    """Insert a row into the audit_log table.

    Args:
        client: An httpx.AsyncClient instance.
        user_id: Supabase auth user UUID.
        expert: Expert slug used.
        mode: 'offline' or 'online'.
        query: The original user query (stored for audit purposes).
        jurisdiction: Jurisdiction if the law expert was used.
        emergency_triggered: Whether the emergency detector fired.
        success: Whether the request completed successfully.
    """
    from app.database import is_local_mode, get_connection
    if is_local_mode(settings.SUPABASE_URL):
        import uuid
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO audit_log (id, user_id, expert, mode, query, jurisdiction, emergency_triggered, success) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), user_id, expert, mode, query, jurisdiction, 1 if emergency_triggered else 0, 1 if success else 0)
            )
            conn.commit()
        except Exception as exc:
            logger.error("Failed to write SQLite audit_log: %s", exc)
        finally:
            conn.close()
        return

    url = f"{settings.SUPABASE_URL}/rest/v1/audit_log"
    payload = {
        "user_id": user_id,
        "expert": expert,
        "mode": mode,
        "query": query,
        "jurisdiction": jurisdiction,
        "emergency_triggered": emergency_triggered,
        "success": success,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        resp = await client.post(url, headers=_headers(), json=payload)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Failed to write audit_log: %s", exc)


async def check_rate_limit(
    client: httpx.AsyncClient,
    user_id: str,
    daily_cap: int,
    window_hours: int,
) -> bool:
    """Check whether a user is still under the offline rate limit.

    Counts usage_log rows for the user within the sliding window.

    Args:
        client: An httpx.AsyncClient instance.
        user_id: Supabase auth user UUID.
        daily_cap: Maximum requests allowed in the window.
        window_hours: Size of the sliding window in hours.

    Returns:
        True if the user is under the limit, False if exceeded.
    """
    from app.database import is_local_mode, get_connection
    if is_local_mode(settings.SUPABASE_URL):
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # SQLite stores dates as strings by default or we can filter via datetime
            cursor.execute(
                "SELECT COUNT(id) FROM usage_log WHERE user_id = ? AND mode = 'offline' AND created_at >= ?",
                (user_id, cutoff.strftime("%Y-%m-%d %H:%M:%S"))
            )
            total = cursor.fetchone()[0]
            return total < daily_cap
        except Exception as exc:
            logger.error("SQLite Rate limit check failed: %s", exc)
            return True
        finally:
            conn.close()

    cutoff = datetime.now(timezone.utc).replace(
        microsecond=0,
    )
    # Subtract window_hours manually to avoid importing timedelta at top level
    from datetime import timedelta
    cutoff = cutoff - timedelta(hours=window_hours)

    url = (
        f"{settings.SUPABASE_URL}/rest/v1/usage_log"
        f"?user_id=eq.{user_id}"
        f"&mode=eq.offline"
        f"&created_at=gte.{cutoff.isoformat()}"
        f"&select=id"
    )
    headers = _headers()
    headers["Prefer"] = "count=exact"

    try:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        count_header = resp.headers.get("content-range", "")
        # content-range looks like "0-4/5" or "*/0"
        if "/" in count_header:
            total = int(count_header.split("/")[1])
        else:
            total = len(resp.json())
        return total < daily_cap
    except (httpx.HTTPError, ValueError) as exc:
        logger.error("Rate limit check failed: %s", exc)
        # Fail open on check errors to avoid blocking users
        return True
