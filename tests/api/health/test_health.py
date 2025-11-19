"""Unit tests for health check endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette import status

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_ping_returns_pong(client: TestClient) -> None:
    """Test that the ping endpoint returns 'pong'."""
    response = client.get("/health/ping")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"response": "pong"}


def test_ping_endpoint_accessibility(client: TestClient) -> None:
    """Test that the ping endpoint is accessible."""
    response = client.get("/health/ping")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/json"
