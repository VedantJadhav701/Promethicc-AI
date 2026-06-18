"""RAG retriever backed by Supabase pgvector / full-text search.

v1 uses Postgres full-text search (to_tsvector / plainto_tsquery) since
we may not have a local embedding model. If an embedding function is
available in the future, cosine similarity search can be swapped in.
"""

from __future__ import annotations

import logging

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
    }


async def search(
    client: httpx.AsyncClient,
    namespace: str,
    query: str,
    top_k: int = 5,
) -> list[dict[str, str]]:
    """Retrieve relevant documents from the rag_documents table.

    Uses a Supabase RPC call to a Postgres function that performs
    full-text search scoped to the expert's namespace. Falls back to
    a simple ILIKE query if the RPC is not deployed yet.

    Args:
        client: An httpx.AsyncClient instance.
        namespace: The expert's RAG namespace (e.g. 'med', 'code').
        query: The user's search query.
        top_k: Maximum number of results to return.

    Returns:
        List of dicts with keys: content, source_title, source_url.
    """
    results = await _rpc_search(client, namespace, query, top_k)
    if results is not None:
        return results

    return await _fallback_search(client, namespace, query, top_k)


async def _rpc_search(
    client: httpx.AsyncClient,
    namespace: str,
    query: str,
    top_k: int,
) -> list[dict[str, str]] | None:
    """Attempt full-text search via a Supabase RPC function.

    Args:
        client: An httpx.AsyncClient instance.
        namespace: Expert namespace.
        query: Search query.
        top_k: Max results.

    Returns:
        List of result dicts, or None if the RPC does not exist.
    """
    from app.database import is_local_mode
    if is_local_mode(settings.SUPABASE_URL):
        # Fall through to _fallback_search SQLite implementation
        return None

    url = f"{settings.SUPABASE_URL}/rest/v1/rpc/search_rag_documents"
    payload = {
        "p_namespace": namespace,
        "p_query": query,
        "p_limit": top_k,
    }

    try:
        resp = await client.post(url, headers=_headers(), json=payload)
        if resp.status_code == 404:
            logger.info("RPC search_rag_documents not found, using fallback")
            return None
        resp.raise_for_status()
        return _normalise_rows(resp.json())
    except httpx.HTTPError as exc:
        logger.warning("RPC search failed: %s", exc)
        return None


async def _fallback_search(
    client: httpx.AsyncClient,
    namespace: str,
    query: str,
    top_k: int,
) -> list[dict[str, str]]:
    """Simple ILIKE keyword search as a fallback.

    Args:
        client: An httpx.AsyncClient instance.
        namespace: Expert namespace.
        query: Search query.
        top_k: Max results.

    Returns:
        List of result dicts.
    """
    from app.database import is_local_mode, get_connection
    if is_local_mode(settings.SUPABASE_URL):
        conn = get_connection()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        try:
            cursor.execute(
                "SELECT content, source_title, source_url FROM rag_documents WHERE expert = ? AND content LIKE ? LIMIT ?",
                (namespace, search_term, top_k)
            )
            rows = cursor.fetchall()
            return [
                {
                    "content": r["content"],
                    "source_title": r["source_title"],
                    "source_url": r["source_url"] or "",
                }
                for r in rows
            ]
        except Exception as exc:
            logger.error("SQLite RAG search failed: %s", exc)
            return []
        finally:
            conn.close()

    search_term = f"%{query}%"
    url = (
        f"{settings.SUPABASE_URL}/rest/v1/rag_documents"
        f"?expert=eq.{namespace}"
        f"&content=ilike.{search_term}"
        f"&select=content,source_title,source_url"
        f"&limit={top_k}"
    )

    try:
        resp = await client.get(url, headers=_headers())
        resp.raise_for_status()
        return _normalise_rows(resp.json())
    except httpx.HTTPError as exc:
        logger.warning("Fallback RAG search failed: %s", exc)
        return []


def _normalise_rows(rows: list[dict]) -> list[dict[str, str]]:
    """Ensure consistent key names in returned rows.

    Args:
        rows: Raw database rows.

    Returns:
        Normalised list of dicts with content, source_title, source_url.
    """
    return [
        {
            "content": row.get("content", ""),
            "source_title": row.get("source_title", ""),
            "source_url": row.get("source_url", ""),
        }
        for row in rows
    ]
