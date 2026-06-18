"""Tests for the RAG retriever module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.rag import retriever


@pytest.mark.asyncio
async def test_fallback_search() -> None:
    """Fallback search should query supabase table using ilike and correct params."""
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "content": "In Python, iteration is typically handled using 'for' loops...",
            "source_title": "python iteration",
            "source_url": "https://example.com/python-iter",
        }
    ]
    mock_resp.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_resp

    results = await retriever._fallback_search(
        mock_client,
        "code",
        "python iteration",
        top_k=5,
    )

    assert len(results) == 1
    assert results[0]["content"] == "In Python, iteration is typically handled using 'for' loops..."
    assert results[0]["source_title"] == "python iteration"
    assert results[0]["source_url"] == "https://example.com/python-iter"

    mock_client.get.assert_called_once()
    called_url = mock_client.get.call_args[0][0]
    assert "rag_documents" in called_url
    assert "expert=eq.code" in called_url
    assert "content=ilike." in called_url


@pytest.mark.asyncio
async def test_rpc_search_success() -> None:
    """RPC search should attempt to query the search_rag_documents rpc endpoint."""
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "content": "Ohm's Law: V = IR",
            "source_title": "ohm's law",
            "source_url": "https://example.com/ohms-law",
        }
    ]
    mock_resp.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_resp

    results = await retriever._rpc_search(
        mock_client,
        "eng",
        "ohm's law",
        top_k=3,
    )

    assert results is not None
    assert len(results) == 1
    assert results[0]["content"] == "Ohm's Law: V = IR"

    mock_client.post.assert_called_once()
    called_url = mock_client.post.call_args[0][0]
    assert "rpc/search_rag_documents" in called_url
    called_payload = mock_client.post.call_args[1]["json"]
    assert called_payload["p_namespace"] == "eng"
    assert called_payload["p_query"] == "ohm's law"
    assert called_payload["p_limit"] == 3


@pytest.mark.asyncio
async def test_search_falls_back_on_rpc_missing() -> None:
    """If RPC endpoint returns 404, search should fall back to _fallback_search."""
    mock_client = AsyncMock()

    # RPC returns 404
    mock_rpc_resp = MagicMock()
    mock_rpc_resp.status_code = 404
    mock_rpc_resp.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_rpc_resp

    # Fallback returns data
    mock_fallback_resp = MagicMock()
    mock_fallback_resp.status_code = 200
    mock_fallback_resp.json.return_value = [
        {"content": "fallthrough", "source_title": "test", "source_url": ""}
    ]
    mock_fallback_resp.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_fallback_resp

    results = await retriever.search(mock_client, "med", "symptoms", top_k=5)

    assert len(results) == 1
    assert results[0]["content"] == "fallthrough"
    mock_client.post.assert_called_once()
    mock_client.get.assert_called_once()
