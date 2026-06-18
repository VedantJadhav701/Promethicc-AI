"""JWT verification and FastAPI authentication dependency."""

from __future__ import annotations

import logging

import jwt
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class User(BaseModel):
    """Authenticated user extracted from a Supabase JWT.

    Attributes:
        id: Supabase auth user UUID.
        email: User email if present in the token claims.
    """

    id: str
    email: str | None = None


async def verify_jwt(token: str) -> dict:
    """Decode and verify a Supabase-issued JWT.

    Args:
        token: Raw JWT string (without the 'Bearer ' prefix).

    Returns:
        Decoded token claims as a dictionary.

    Raises:
        HTTPException: 401 if the token is expired, malformed, or invalid.
    """
    try:
        from app.database import is_local_mode
        if is_local_mode(settings.SUPABASE_URL):
            # In local mode, bypass signature verification to support mock tokens
            return jwt.decode(token, options={"verify_signature": False})

        decoded: dict = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return decoded
    except jwt.ExpiredSignatureError:
        logger.warning("JWT expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid JWT: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


async def get_current_user(
    authorization: str = Header(..., description="Bearer <JWT>"),
) -> User:
    """FastAPI dependency that extracts the current user from the Authorization header.

    Args:
        authorization: The full Authorization header value (e.g. 'Bearer eyJ...').

    Returns:
        A User instance populated from the JWT claims.

    Raises:
        HTTPException: 401 if the header is missing, malformed, or the JWT is invalid.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
        )

    token = authorization[len("Bearer "):]
    claims = await verify_jwt(token)

    return User(
        id=claims.get("sub", ""),
        email=claims.get("email"),
    )
