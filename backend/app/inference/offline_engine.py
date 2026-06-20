"""Offline inference engine using llama-cpp-python.

Loads a single shared GGUF model once at startup (lazy singleton).
Inference runs in a thread pool so the async event loop stays free.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_model: object | None = None  # typed as object to avoid import error when llama-cpp not installed


def _load_model() -> object:
    """Load the GGUF model from disk into a llama_cpp.Llama instance.

    Returns:
        A llama_cpp.Llama model instance.

    Raises:
        HTTPException: 503 if the model file is missing or loading fails.
    """
    try:
        from llama_cpp import Llama  # type: ignore[import-untyped]
    except ImportError:
        logger.error("llama-cpp-python is not installed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Offline model runtime is not available",
        )

    try:
        import os
        cpu_count = os.cpu_count() or 4
        # Optimize thread count for hybrid CPUs (like Intel Alder Lake) to prevent E-core latency
        threads = max(1, cpu_count // 2 if cpu_count > 4 else cpu_count)

        model = Llama(
            model_path=settings.MODEL_PATH,
            n_ctx=settings.MODEL_CONTEXT_SIZE,
            n_threads=threads,
            verbose=False,
        )
        logger.info("GGUF model loaded from %s (n_threads=%d)", settings.MODEL_PATH, threads)
        return model
    except Exception as exc:
        logger.error("Failed to load GGUF model: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Offline model could not be loaded",
        )


def _get_model() -> object:
    """Return the cached model, loading it on first access.

    Returns:
        The loaded Llama model instance.
    """
    global _model  # noqa: PLW0603
    if _model is None:
        _model = _load_model()
    return _model


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def _build_messages(
    system_prompt: str,
    rag_context: str | None,
    message: str,
) -> list[dict[str, str]]:
    """Build a ChatML-style messages array for the model.

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


# ---------------------------------------------------------------------------
# Blocking inference (runs in thread pool)
# ---------------------------------------------------------------------------


def _run_inference(messages: list[dict[str, str]]) -> tuple[str, int]:
    """Execute synchronous llama.cpp inference.

    Args:
        messages: ChatML messages array.

    Returns:
        Tuple of (response_text, tokens_used).
    """
    import time
    model = _get_model()

    start_time = time.perf_counter()
    result = model.create_chat_completion(  # type: ignore[union-attr]
        messages=messages,
        max_tokens=settings.MODEL_MAX_TOKENS,
        temperature=0.7,
    )
    duration = time.perf_counter() - start_time

    text: str = result["choices"][0]["message"]["content"]  # type: ignore[index]
    tokens: int = result.get("usage", {}).get("total_tokens", 0)  # type: ignore[union-attr]

    tps = tokens / duration if duration > 0 else 0
    logger.info(
        "Offline inference completed: %d tokens generated in %.2f seconds (%.2f tokens/sec)",
        tokens,
        duration,
        tps,
    )
    return text.strip(), tokens


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------


async def generate(
    system_prompt: str,
    rag_context: str | None,
    message: str,
) -> tuple[str, int]:
    """Generate a response using the offline GGUF model.

    Wraps the blocking llama.cpp call in asyncio.to_thread so the
    FastAPI event loop is never blocked.

    Args:
        system_prompt: Expert-specific system prompt.
        rag_context: Optional RAG context string.
        message: The user's query.

    Returns:
        Tuple of (response_text, tokens_used).

    Raises:
        HTTPException: 503 if the model is not loaded.
    """
    messages = _build_messages(system_prompt, rag_context, message)
    return await asyncio.to_thread(_run_inference, messages)
