"""Health check routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from wf_catalogue_service.api.health.schemas import HealthResponse
from wf_catalogue_service.db.session import get_session

health_router = APIRouter(tags=["Health"])


@health_router.get("/health", response_model=HealthResponse)
async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> HealthResponse:
    """Health check endpoint.

    Verifies database connectivity.

    """
    try:
        await session.execute(text("SELECT 1"))
        return HealthResponse(status="ok")
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable") from err
