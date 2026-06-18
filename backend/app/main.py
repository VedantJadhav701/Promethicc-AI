"""FastAPI application entry point for Promethicc AI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler for startup/shutdown events.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control back to the framework after startup tasks complete.
    """
    logger.info("Promethicc AI backend starting up")
    logger.info("Offline model will be loaded lazily on first request")
    yield
    logger.info("Promethicc AI backend shutting down")


app = FastAPI(
    title="Promethicc AI",
    description=(
        "Hybrid AI expert platform with offline (free) and online (paid) modes. "
        "Specialised experts: Code, Eng, Agri, Med, Law."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and monitoring.

    Returns:
        A dict indicating the service is healthy.
    """
    return {"status": "healthy"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning service metadata.

    Returns:
        Service name, version, and status.
    """
    return {
        "name": "Promethicc AI",
        "version": "1.0.0",
        "status": "running",
    }
