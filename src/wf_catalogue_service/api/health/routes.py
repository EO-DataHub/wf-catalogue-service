"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter

from wf_catalogue_service.api.health.schemas import HealthPingResponse

health_router = APIRouter(prefix="/health", tags=["Health Check"])


@health_router.get(
    "/ping",
    response_model=HealthPingResponse,
    summary="Health check endpoint.",
)
async def ping() -> HealthPingResponse:
    """Health-check endpoint."""
    return HealthPingResponse(response="pong")
