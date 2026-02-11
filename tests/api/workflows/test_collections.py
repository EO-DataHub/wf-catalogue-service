"""Tests for collections endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from starlette import status

if TYPE_CHECKING:
    from httpx import AsyncClient

CATALOGUE_ID = "eodh-workflows-notebooks"
AUTH_HEADER = {"Authorization": "Bearer test-token"}


@pytest.mark.asyncio
async def test_get_collections_returns_list(client: AsyncClient) -> None:
    """Test that GET /collections returns list of catalogues."""
    response = await client.get("/collections", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == CATALOGUE_ID
    assert data[0]["type"] == "Collection"


@pytest.mark.asyncio
async def test_get_collections_without_auth_returns_403(client: AsyncClient) -> None:
    """Test that GET /collections without auth returns 403."""
    response = await client.get("/collections")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_catalogue_returns_details(client: AsyncClient) -> None:
    """Test that GET /collections/{id} returns catalogue details."""
    response = await client.get(f"/collections/{CATALOGUE_ID}", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == CATALOGUE_ID
    assert data["type"] == "Collection"
    assert data["title"] == "EODH Workflows and Notebooks Catalog"


@pytest.mark.asyncio
async def test_get_catalogue_not_found(client: AsyncClient) -> None:
    """Test that GET /collections/{id} returns 404 for unknown catalogue."""
    response = await client.get("/collections/unknown-catalogue", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_items_returns_empty_list(client: AsyncClient) -> None:
    """Test that GET /collections/{id}/items returns empty list initially."""
    response = await client.get(f"/collections/{CATALOGUE_ID}/items", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["total_items"] == 0


@pytest.mark.asyncio
async def test_get_item_not_found(client: AsyncClient) -> None:
    """Test that GET /collections/{id}/items/{id} returns 404 for unknown record."""
    response = await client.get(f"/collections/{CATALOGUE_ID}/items/unknown-record", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_collection_returns_201(client: AsyncClient) -> None:
    """Test that POST /collections creates a new catalogue."""
    response = await client.post(
        "/collections",
        json={"id": "test-collection", "title": "Test", "description": "Test collection"},
        headers=AUTH_HEADER,
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == "test-collection"
    assert data["type"] == "Collection"
    assert data["title"] == "Test"


@pytest.mark.asyncio
async def test_create_collection_duplicate_returns_409(client: AsyncClient) -> None:
    """Test that POST /collections with existing ID returns 409."""
    response = await client.post(
        "/collections",
        json={"id": CATALOGUE_ID, "title": "Duplicate", "description": "Duplicate"},
        headers=AUTH_HEADER,
    )

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_delete_collection_returns_204(client: AsyncClient) -> None:
    """Test that DELETE /collections/{id} deletes an empty catalogue."""
    await client.post(
        "/collections",
        json={"id": "to-delete", "title": "Delete me", "description": "Temporary"},
        headers=AUTH_HEADER,
    )
    response = await client.delete("/collections/to-delete", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_collection_not_found_returns_404(client: AsyncClient) -> None:
    """Test that DELETE /collections/{id} returns 404 for unknown catalogue."""
    response = await client.delete("/collections/nonexistent", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_collection_with_records_returns_409(client: AsyncClient, workflow_json: dict[str, Any]) -> None:
    """Test that DELETE /collections/{id} returns 409 if catalogue has records."""
    await client.post("/register", json=workflow_json, headers=AUTH_HEADER)
    response = await client.delete(f"/collections/{CATALOGUE_ID}", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_409_CONFLICT
