"""Online inference engine via an external OpenAI-compatible API.

Used for paid-tier requests. Calls an external LLM (Groq, Gemini, etc.)
through the standard /chat/completions endpoint.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(timeout=60.0, connect=10.0)


def _build_messages(
    system_prompt: str,
    rag_context: str | None,
    message: str,
) -> list[dict[str, str]]:
    """Build an OpenAI-style messages array.

    Args:
        system_prompt: Expert-specific system prompt.
        rag_context: Optional retrieved context to prepend.
        message: The user's query.

    Returns:
        List of role/content message dicts.
    """
    system_content = system_prompt
    if rag_context:
        system_content += (
            "\n\n--- Retrieved Context ---\n"
            f"{rag_context}\n"
            "--- End Context ---"
        )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": message},
    ]


async def generate(
    system_prompt: str,
    rag_context: str | None,
    message: str,
) -> tuple[str, int]:
    """Generate a response using an external OpenAI-compatible API.

    Args:
        system_prompt: Expert-specific system prompt.
        rag_context: Optional RAG context string.
        message: The user's query.

    Returns:
        Tuple of (response_text, tokens_used).

    Raises:
        HTTPException: 502 if the upstream API call fails.
    """
    messages = _build_messages(system_prompt, rag_context, message)

    headers = {
        "Authorization": f"Bearer {settings.ONLINE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.ONLINE_MODEL,
        "messages": messages,
        "max_tokens": settings.MODEL_MAX_TOKENS,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.ONLINE_API_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error("Online API HTTP error: %s %s", exc.response.status_code, exc.response.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Online inference provider returned an error",
        )
    except httpx.RequestError as exc:
        logger.error("Online API request error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach online inference provider",
        )

    data: dict = resp.json()
    text: str = data["choices"][0]["message"]["content"]
    tokens: int = data.get("usage", {}).get("total_tokens", 0)

    return text.strip(), tokens
