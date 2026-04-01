"""GET /health – liveness check endpoint."""

from __future__ import annotations

import logging
from typing import Dict

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ops"])


@router.get("/health")
async def health() -> Dict[str, str]:
    logger.info("Health check")
    return {"status": "ok", "service": "customer-support-engine"}
