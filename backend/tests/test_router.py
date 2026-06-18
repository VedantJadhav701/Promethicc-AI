"""Tests for the main API router logic.

All inference engines and Supabase calls are mocked so tests run
without external dependencies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import User, get_current_user
from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEST_USER = User(id="00000000-0000-0000-0000-000000000001", email="test@example.com")


def _make_client(user: User = _TEST_USER) -> TestClient:
    """Build a TestClient with the auth dependency overridden.

    Args:
        user: The User to inject for all authenticated requests.

    Returns:
        A FastAPI TestClient.
    """
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _chat_payload(
    expert: str = "code",
    mode: str = "offline",
    message: str = "Hello",
    jurisdiction: str | None = None,
) -> dict:
    """Build a standard chat request payload.

    Args:
        expert: Expert slug.
        mode: Inference mode.
        message: User message.
        jurisdiction: Optional jurisdiction for law.

    Returns:
        Dict suitable for POST /v1/chat.
    """
    payload: dict = {"expert": expert, "mode": mode, "message": message}
    if jurisdiction is not None:
        payload["jurisdiction"] = jurisdiction
    return payload


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestUnknownExpert:
    """Unknown expert slug should return 404."""

    def test_returns_404(self) -> None:
        """POST /v1/chat with a non-existent expert returns 404."""
        client = _make_client()
        resp = client.post("/v1/chat", json=_chat_payload(expert="nonexistent"))
        assert resp.status_code == 404
        body = resp.json()
        assert body["detail"]["code"] == "UNKNOWN_EXPERT"


class TestDisclaimerRequired:
    """High-stakes expert without accepted disclaimer should return 403."""

    def test_med_without_disclaimer_returns_403(self) -> None:
        """POST /v1/chat for med without disclaimer acceptance returns 403."""
        client = _make_client()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("app.safety.disclaimers.httpx.AsyncClient") as mock_cls:
            mock_ctx = AsyncMock()
            mock_ctx.get.return_value = mock_response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("app.router._supabase_client") as mock_sb:
                sb_client = AsyncMock()
                sb_client.get.return_value = mock_response
                sb_client.__aenter__ = AsyncMock(return_value=sb_client)
                sb_client.__aexit__ = AsyncMock(return_value=False)
                mock_sb.return_value = sb_client

                resp = client.post("/v1/chat", json=_chat_payload(expert="med"))

        assert resp.status_code == 403
        body = resp.json()
        assert body["detail"]["code"] == "DISCLAIMER_REQUIRED"


class TestJurisdictionRequired:
    """Law expert without jurisdiction should return 400."""

    def test_law_without_jurisdiction_returns_400(self) -> None:
        """POST /v1/chat for law without jurisdiction returns 400."""
        client = _make_client()

        # Mock disclaimer as accepted so we get past that check
        mock_response_accepted = MagicMock()
        mock_response_accepted.status_code = 200
        mock_response_accepted.json.return_value = [{"id": 1}]
        mock_response_accepted.raise_for_status = MagicMock()

        with patch("app.router._supabase_client") as mock_sb:
            sb_client = AsyncMock()
            sb_client.get.return_value = mock_response_accepted
            sb_client.__aenter__ = AsyncMock(return_value=sb_client)
            sb_client.__aexit__ = AsyncMock(return_value=False)
            mock_sb.return_value = sb_client

            resp = client.post("/v1/chat", json=_chat_payload(expert="law"))

        assert resp.status_code == 400
        body = resp.json()
        assert body["detail"]["code"] == "JURISDICTION_REQUIRED"


class TestUpgradeRequired:
    """Free user requesting online mode should return 403."""

    def test_free_user_online_returns_403(self) -> None:
        """POST /v1/chat with mode=online for a free user returns 403."""
        client = _make_client()

        # Mock: no profile found (free user)
        mock_empty = MagicMock()
        mock_empty.status_code = 200
        mock_empty.json.return_value = []
        mock_empty.raise_for_status = MagicMock()
        mock_empty.headers = {"content-range": "*/0"}

        with patch("app.router._supabase_client") as mock_sb:
            sb_client = AsyncMock()
            sb_client.get.return_value = mock_empty
            sb_client.__aenter__ = AsyncMock(return_value=sb_client)
            sb_client.__aexit__ = AsyncMock(return_value=False)
            mock_sb.return_value = sb_client

            resp = client.post(
                "/v1/chat",
                json=_chat_payload(expert="code", mode="online"),
            )

        assert resp.status_code == 403
        body = resp.json()
        assert body["detail"]["code"] == "UPGRADE_REQUIRED"


class TestRateLimitExceeded:
    """User who has exceeded the offline rate limit should get 429."""

    def test_rate_limited_returns_429(self) -> None:
        """POST /v1/chat when rate limit is exceeded returns 429."""
        client = _make_client()

        # Mock: rate limit check returns over-limit
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": i} for i in range(60)]
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-range": "0-59/60"}

        with patch("app.router._supabase_client") as mock_sb:
            sb_client = AsyncMock()
            sb_client.get.return_value = mock_response
            sb_client.__aenter__ = AsyncMock(return_value=sb_client)
            sb_client.__aexit__ = AsyncMock(return_value=False)
            mock_sb.return_value = sb_client

            resp = client.post(
                "/v1/chat",
                json=_chat_payload(expert="code", mode="offline"),
            )

        assert resp.status_code == 429
        body = resp.json()
        assert body["detail"]["code"] == "RATE_LIMIT_EXCEEDED"


class TestExpertsEndpoint:
    """GET /v1/experts should be public and return expert metadata."""

    def test_list_experts_returns_all(self) -> None:
        """GET /v1/experts returns all configured experts."""
        client = TestClient(app)
        resp = client.get("/v1/experts")
        assert resp.status_code == 200
        data = resp.json()
        slugs = {e["slug"] for e in data}
        assert {"code", "eng", "agri", "med", "law"} == slugs


class TestHealthEndpoint:
    """Health check should always return 200."""

    def test_health_returns_200(self) -> None:
        """GET /health returns healthy status."""
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestRootEndpoint:
    """Root endpoint should return service metadata."""

    def test_root_returns_metadata(self) -> None:
        """GET / returns service name, version, status."""
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Promethicc AI"
        assert body["version"] == "1.0.0"
        assert body["status"] == "running"
