"""Health schemas."""

from __future__ import annotations

from pydantic import BaseModel


class HealthPingResponse(BaseModel):
    """Health ping response."""

    response: str
