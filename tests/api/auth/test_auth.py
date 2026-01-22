"""Tests for authentication."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient, workflow_json: Any) -> None:
    """Test that invalid token returns 401 Unauthorized."""
    mock_settings = MagicMock()
    mock_settings.environment = "prod"

    with (
        patch("wf_catalogue_service.api.auth.helpers.current_settings", return_value=mock_settings),
        patch("wf_catalogue_service.api.auth.helpers.decode_token") as mock_decode,
    ):
        mock_decode.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        response = await client.post(
            "/register",
            json=workflow_json,
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        mock_decode.assert_called_once_with("invalid-token")


@pytest.mark.asyncio
async def test_valid_token_allows_request(client: AsyncClient, workflow_json: Any) -> None:
    """Test that valid token allows the request."""
    mock_settings = MagicMock()
    mock_settings.environment = "prod"

    with (
        patch("wf_catalogue_service.api.auth.helpers.current_settings", return_value=mock_settings),
        patch("wf_catalogue_service.api.auth.helpers.decode_token") as mock_decode,
    ):
        mock_decode.return_value = {"sub": "user123"}

        response = await client.post(
            "/register",
            json=workflow_json,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        mock_decode.assert_called_once_with("valid-token")
