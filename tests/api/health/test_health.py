"""Tests for health check endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from starlette import status

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    """Test that health endpoint returns ok when database is connected."""
    response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
