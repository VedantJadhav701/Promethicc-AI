"""Pytest fixtures shared across the test suite."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auth import User


@pytest.fixture
def test_user() -> User:
    """Create a test user for authenticated endpoint tests.

    Returns:
        A User instance with a deterministic UUID and email.
    """
    return User(id="00000000-0000-0000-0000-000000000001", email="test@example.com")


@pytest.fixture
def mock_supabase_client() -> AsyncMock:
    """Create a mock httpx.AsyncClient that simulates Supabase responses.

    Returns:
        An AsyncMock configured with sensible defaults for Supabase REST calls.
    """
    client = AsyncMock()

    # Default GET response: empty list
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.json.return_value = []
    get_response.raise_for_status = MagicMock()
    get_response.headers = {"content-range": "*/0"}
    client.get.return_value = get_response

    # Default POST response: success
    post_response = MagicMock()
    post_response.status_code = 201
    post_response.raise_for_status = MagicMock()
    client.post.return_value = post_response

    return client


@pytest.fixture
def mock_settings() -> dict[str, Any]:
    """Provide overridable test settings.

    Returns:
        Dict of setting key-value pairs for testing.
    """
    return {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_KEY": "test-service-key",
        "SUPABASE_JWT_SECRET": "test-jwt-secret",
        "MODEL_PATH": "./models/test.gguf",
        "ONLINE_API_KEY": "test-api-key",
        "ONLINE_API_URL": "https://api.test.com/v1",
        "ONLINE_MODEL": "test-model",
        "DAILY_OFFLINE_CAP": 50,
        "RATE_LIMIT_WINDOW_HOURS": 24,
        "MODEL_MAX_TOKENS": 512,
        "MODEL_CONTEXT_SIZE": 2048,
    }
