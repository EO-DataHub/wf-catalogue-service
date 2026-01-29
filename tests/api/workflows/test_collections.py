"""Tests for collections endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from starlette import status

if TYPE_CHECKING:
    from httpx import AsyncClient

CATALOGUE_ID = "eodh-workflows-notebooks"


@pytest.mark.asyncio
async def test_get_collections_returns_list(client: AsyncClient) -> None:
    """Test that GET /collections returns list of catalogues."""
    response = await client.get("/collections")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == CATALOGUE_ID
    assert data[0]["type"] == "Collection"


@pytest.mark.asyncio
async def test_get_catalogue_returns_details(client: AsyncClient) -> None:
    """Test that GET /collections/{id} returns catalogue details."""
    response = await client.get(f"/collections/{CATALOGUE_ID}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == CATALOGUE_ID
    assert data["type"] == "Collection"
    assert data["title"] == "EODH Workflows and Notebooks Catalog"


@pytest.mark.asyncio
async def test_get_catalogue_not_found(client: AsyncClient) -> None:
    """Test that GET /collections/{id} returns 404 for unknown catalogue."""
    response = await client.get("/collections/unknown-catalogue")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_items_returns_empty_list(client: AsyncClient) -> None:
    """Test that GET /collections/{id}/items returns empty list initially."""
    response = await client.get(f"/collections/{CATALOGUE_ID}/items")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["total_items"] == 0


@pytest.mark.asyncio
async def test_get_item_not_found(client: AsyncClient) -> None:
    """Test that GET /collections/{id}/items/{id} returns 404 for unknown record."""
    response = await client.get(f"/collections/{CATALOGUE_ID}/items/unknown-record")

    assert response.status_code == status.HTTP_404_NOT_FOUND
