"""
PaveX – Auth API stub
backend/app/api/auth.py

Placeholder for future authentication. Currently provides:
  - GET /auth/status  — confirms the auth module is reachable
  - X-API-Key header validation helper (commented-out template)

To enable real API-key auth:
  1. Set API_KEY=<secret> in backend/.env
  2. Uncomment the `verify_api_key` dependency below
  3. Add `dependencies=[Depends(verify_api_key)]` to sensitive routers
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

# ---------------------------------------------------------------------------
# Optional API-key header scheme (inactive until API_KEY env var is set)
# ---------------------------------------------------------------------------

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_EXPECTED_KEY: str | None = os.getenv("API_KEY")


async def verify_api_key(api_key: str | None = Security(_API_KEY_HEADER)) -> None:
    """
    FastAPI dependency — protects an endpoint with a static API key.
    Inactive when API_KEY env var is not set (returns immediately).

    Usage:
        @router.get("/protected", dependencies=[Depends(verify_api_key)])
    """
    if not _EXPECTED_KEY:
        # Auth not configured — open access (dev mode)
        return
    if api_key != _EXPECTED_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status", summary="Auth module health check")
async def auth_status():
    """Returns auth configuration state. Does not expose key material."""
    return {
        "auth_enabled": bool(_EXPECTED_KEY),
        "scheme": "X-API-Key header" if _EXPECTED_KEY else "none (open access)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
