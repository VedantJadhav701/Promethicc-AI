"""Main API router for Promethicc AI.

Implements the full chat flow: auth → expert lookup → disclaimer gate →
emergency detection → tier check → rate limit → RAG → inference → audit.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel

from app.auth import User, get_current_user
from app.config import experts, settings
from app.safety import emergency_detector
from app.safety.disclaimers import DISCLAIMERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["v1"])

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Incoming chat request payload.

    Attributes:
        expert: Expert slug (e.g. 'code', 'med').
        mode: Inference mode — 'offline' (free) or 'online' (paid).
        message: The user's query text.
        jurisdiction: Required when expert is 'law'.
    """

    expert: str
    mode: Literal["offline", "online"]
    message: str
    jurisdiction: str | None = None


class ChatResponse(BaseModel):
    """Successful chat response payload.

    Attributes:
        response: The generated text.
        sources: List of source URLs from RAG retrieval.
        mode: The inference mode used.
        expert: The expert slug used.
    """

    response: str
    sources: list[str]
    mode: str
    expert: str


class ErrorResponse(BaseModel):
    """Structured error response.

    Attributes:
        error: Human-readable error message.
        code: Machine-readable error code.
    """

    error: str
    code: str


# ---------------------------------------------------------------------------
# Shared httpx client (created per-request to avoid lifecycle issues)
# ---------------------------------------------------------------------------


def _supabase_client() -> httpx.AsyncClient:
    """Create an httpx.AsyncClient for Supabase REST calls.

    Returns:
        A new AsyncClient instance.
    """
    return httpx.AsyncClient(timeout=httpx.Timeout(15.0))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _check_online_eligibility(
    client: httpx.AsyncClient,
    user_id: str,
) -> bool:
    """Verify that a user has an active subscription or credits for online mode.

    Args:
        client: httpx.AsyncClient for Supabase.
        user_id: The authenticated user's UUID.

    Returns:
        True if the user is eligible for online mode.
    """
    url = (
        f"{settings.SUPABASE_URL}/rest/v1/profiles"
        f"?id=eq.{user_id}"
        f"&select=tier,credits"
    )
    headers = {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
    }
    try:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        rows: list[dict] = resp.json()
        if not rows:
            return False
        profile = rows[0]
        tier: str = profile.get("tier", "free")
        credits: int = profile.get("credits", 0)
        return tier == "paid" or credits > 0
    except httpx.HTTPError as exc:
        logger.error("Profile check failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# POST /v1/chat — main endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
)
async def chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
) -> ChatResponse | ErrorResponse:
    """Process a chat request through the full Promethicc AI pipeline.

    Args:
        req: The chat request payload.
        user: The authenticated user (injected via dependency).

    Returns:
        A ChatResponse on success, or raises an HTTPException.
    """
    return await _handle_chat(req, user)


async def _handle_chat(req: ChatRequest, user: User) -> ChatResponse:
    """Inner handler split out to respect the ~40-line function limit.

    Args:
        req: The chat request payload.
        user: The authenticated user.

    Returns:
        A ChatResponse on success.

    Raises:
        HTTPException: On validation failures, rate limiting, or tier issues.
    """
    # 1. Look up expert
    expert_cfg = experts.get(req.expert)
    if expert_cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Unknown expert: {req.expert}", "code": "UNKNOWN_EXPERT"},
        )

    async with _supabase_client() as client:
        # 2. Disclaimer gate for high-stakes experts
        if expert_cfg.risk_tier == "high_stakes":
            await _enforce_disclaimer(client, user.id, req.expert)

        # 3. Jurisdiction check for law
        if req.expert == "law" and not req.jurisdiction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Jurisdiction is required for law queries", "code": "JURISDICTION_REQUIRED"},
            )

        # 4. Emergency detection for high-stakes experts
        if expert_cfg.risk_tier == "high_stakes":
            triggered, safe_response = await emergency_detector.check(req.message)
            if triggered:
                await _audit_emergency(client, user.id, req, safe_response)
                return ChatResponse(
                    response=safe_response,  # type: ignore[arg-type]
                    sources=[],
                    mode=req.mode,
                    expert=req.expert,
                )

        # 5. Online mode tier check
        if req.mode == "online":
            await _enforce_online_tier(client, user.id)

        # 6. Rate limit for offline mode
        if req.mode == "offline":
            await _enforce_rate_limit(client, user.id)

        # 7. RAG retrieval
        rag_context, sources = await _retrieve_context(client, expert_cfg.rag_namespace, req)

        # 8. Inference dispatch
        response_text, tokens_used = await _dispatch_inference(expert_cfg, rag_context, req)

        # 9. Audit + usage logging
        await _post_inference_logging(client, user.id, req, tokens_used)

    return ChatResponse(
        response=response_text,
        sources=sources,
        mode=req.mode,
        expert=req.expert,
    )


async def _enforce_disclaimer(
    client: httpx.AsyncClient,
    user_id: str,
    expert: str,
) -> None:
    """Raise 403 if the user has not accepted the disclaimer.

    Args:
        client: httpx.AsyncClient for Supabase.
        user_id: User UUID.
        expert: Expert slug.
    """
    from app.safety.disclaimers import check_disclaimer_accepted

    accepted = await check_disclaimer_accepted(client, user_id, expert)
    if not accepted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "You must accept the disclaimer before using this expert",
                "code": "DISCLAIMER_REQUIRED",
                "disclaimer": DISCLAIMERS.get(expert, ""),
            },
        )


async def _enforce_online_tier(
    client: httpx.AsyncClient,
    user_id: str,
) -> None:
    """Raise 403 if the user is not eligible for online mode.

    Args:
        client: httpx.AsyncClient for Supabase.
        user_id: User UUID.
    """
    eligible = await _check_online_eligibility(client, user_id)
    if not eligible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Online mode requires a paid subscription or credits",
                "code": "UPGRADE_REQUIRED",
            },
        )


async def _enforce_rate_limit(
    client: httpx.AsyncClient,
    user_id: str,
) -> None:
    """Raise 429 if the user has exceeded their offline rate limit.

    Args:
        client: httpx.AsyncClient for Supabase.
        user_id: User UUID.
    """
    from app.audit import check_rate_limit

    under_limit = await check_rate_limit(
        client,
        user_id,
        settings.DAILY_OFFLINE_CAP,
        settings.RATE_LIMIT_WINDOW_HOURS,
    )
    if not under_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Offline rate limit exceeded. Please try again later.",
                "code": "RATE_LIMIT_EXCEEDED",
            },
        )


async def _retrieve_context(
    client: httpx.AsyncClient,
    namespace: str,
    req: ChatRequest,
) -> tuple[str | None, list[str]]:
    """Retrieve RAG context for the query.

    Args:
        client: httpx.AsyncClient for Supabase.
        namespace: Expert RAG namespace.
        req: The original chat request.

    Returns:
        Tuple of (rag_context_string, source_urls).
    """
    from app.rag import retriever

    docs = await retriever.search(client, namespace, req.message)
    if not docs:
        return None, []

    context_parts = [d["content"] for d in docs if d.get("content")]
    sources = [d["source_url"] for d in docs if d.get("source_url")]
    rag_context = "\n\n".join(context_parts) if context_parts else None
    return rag_context, sources


async def _dispatch_inference(
    expert_cfg: object,
    rag_context: str | None,
    req: ChatRequest,
) -> tuple[str, int]:
    """Route inference to the appropriate engine.

    Args:
        expert_cfg: The ExpertConfig for the selected expert.
        rag_context: Optional RAG context string.
        req: The chat request.

    Returns:
        Tuple of (response_text, tokens_used).
    """
    system_prompt: str = expert_cfg.system_prompt  # type: ignore[attr-defined]
    if req.expert == "law" and req.jurisdiction:
        system_prompt += f"\n\nJurisdiction context: {req.jurisdiction}"

    if req.mode == "online":
        from app.inference import online_engine
        return await online_engine.generate(system_prompt, rag_context, req.message)
    else:
        from app.inference import offline_engine
        return await offline_engine.generate(system_prompt, rag_context, req.message)


async def _audit_emergency(
    client: httpx.AsyncClient,
    user_id: str,
    req: ChatRequest,
    safe_response: str | None,
) -> None:
    """Log an emergency-triggered interaction.

    Args:
        client: httpx.AsyncClient for Supabase.
        user_id: User UUID.
        req: The original chat request.
        safe_response: The fixed safe response that was returned.
    """
    from app.audit import log_audit

    await log_audit(
        client,
        user_id=user_id,
        expert=req.expert,
        mode=req.mode,
        query=req.message,
        jurisdiction=req.jurisdiction,
        emergency_triggered=True,
        success=True,
    )


async def _post_inference_logging(
    client: httpx.AsyncClient,
    user_id: str,
    req: ChatRequest,
    tokens_used: int,
) -> None:
    """Write usage and audit log entries after successful inference.

    Args:
        client: httpx.AsyncClient for Supabase.
        user_id: User UUID.
        req: The original chat request.
        tokens_used: Tokens consumed by inference.
    """
    from app.audit import log_audit, log_usage

    await log_usage(client, user_id, req.expert, req.mode, tokens_used)
    await log_audit(
        client,
        user_id=user_id,
        expert=req.expert,
        mode=req.mode,
        query=req.message,
        jurisdiction=req.jurisdiction,
        emergency_triggered=False,
        success=True,
    )


# ---------------------------------------------------------------------------
# POST /v1/disclaimers/{expert}/accept
# ---------------------------------------------------------------------------


@router.post(
    "/disclaimers/{expert}/accept",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def accept_disclaimer_endpoint(
    expert: str,
    user: User = Depends(get_current_user),
):
    """Accept the disclaimer for a high-stakes expert.

    Args:
        expert: Expert slug (e.g. 'med', 'law').
        user: The authenticated user (injected).
    """
    if expert not in DISCLAIMERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"No disclaimer for expert: {expert}", "code": "UNKNOWN_EXPERT"},
        )

    from app.safety.disclaimers import accept_disclaimer

    async with _supabase_client() as client:
        await accept_disclaimer(client, user.id, expert)


# ---------------------------------------------------------------------------
# GET /v1/usage
# ---------------------------------------------------------------------------


@router.get("/usage")
async def get_usage(
    user: User = Depends(get_current_user),
) -> dict:
    """Return usage statistics for the current user.

    Args:
        user: The authenticated user (injected).

    Returns:
        Dict with usage count and limit information.
    """
    from app.audit import check_rate_limit

    async with _supabase_client() as client:
        under_limit = await check_rate_limit(
            client,
            user.id,
            settings.DAILY_OFFLINE_CAP,
            settings.RATE_LIMIT_WINDOW_HOURS,
        )

    return {
        "user_id": user.id,
        "daily_offline_cap": settings.DAILY_OFFLINE_CAP,
        "window_hours": settings.RATE_LIMIT_WINDOW_HOURS,
        "under_limit": under_limit,
    }


# ---------------------------------------------------------------------------
# GET /v1/experts — public, no auth
# ---------------------------------------------------------------------------


@router.get("/experts")
async def list_experts() -> list[dict[str, Any]]:
    """Return a public list of available experts with their metadata.

    Returns:
        List of expert dicts with slug, label, and risk_tier.
    """
    return [
        {
            "slug": slug,
            "label": cfg.label,
            "risk_tier": cfg.risk_tier,
            "has_disclaimer": slug in DISCLAIMERS,
        }
        for slug, cfg in experts.items()
    ]
