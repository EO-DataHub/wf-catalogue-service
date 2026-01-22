"""Tests for registration endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from starlette import status

if TYPE_CHECKING:
    from httpx import AsyncClient

CATALOGUE_ID = "eodh-workflows-notebooks"
AUTH_HEADER = {"Authorization": "Bearer test-token"}


@pytest.mark.asyncio
async def test_register_workflow_returns_201(client: AsyncClient, workflow_json: Any) -> None:
    """Test that POST /register with workflow JSON returns 201."""
    response = await client.post("/register", json=workflow_json, headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == workflow_json["id"]
    assert data["properties"]["type"] == "workflow"
    assert data["properties"]["title"] == workflow_json["properties"]["title"]


@pytest.mark.asyncio
async def test_register_notebook_returns_201(client: AsyncClient, notebook_json: Any) -> None:
    """Test that POST /register with notebook JSON returns 201."""
    response = await client.post("/register", json=notebook_json, headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == notebook_json["id"]
    assert data["properties"]["type"] == "notebook"
    assert data["properties"]["title"] == notebook_json["properties"]["title"]


@pytest.mark.asyncio
async def test_register_without_auth_returns_403(client: AsyncClient, workflow_json: Any) -> None:
    """Test that POST /register without auth returns 403."""
    response = await client.post("/register", json=workflow_json)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_register_duplicate_returns_409(client: AsyncClient, workflow_json: Any) -> None:
    """Test that POST /register with duplicate ID returns 409."""
    await client.post("/register", json=workflow_json, headers=AUTH_HEADER)
    response = await client.post("/register", json=workflow_json, headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_delete_record_returns_204(client: AsyncClient, workflow_json: Any) -> None:
    """Test that DELETE /register/{id} returns 204."""
    await client.post("/register", json=workflow_json, headers=AUTH_HEADER)
    response = await client.delete(f"/register/{workflow_json['id']}", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_not_found_returns_404(client: AsyncClient) -> None:
    """Test that DELETE /register/{id} returns 404 for unknown record."""
    response = await client.delete("/register/unknown-record", headers=AUTH_HEADER)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_full_workflow_flow(client: AsyncClient, workflow_json: Any) -> None:
    """Test full flow: register -> get -> delete."""
    # Register
    response = await client.post("/register", json=workflow_json, headers=AUTH_HEADER)
    assert response.status_code == status.HTTP_201_CREATED

    # Get item
    response = await client.get(f"/collections/{CATALOGUE_ID}/items/{workflow_json['id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == workflow_json["id"]
    assert data["properties"]["title"] == workflow_json["properties"]["title"]

    # List items
    response = await client.get(f"/collections/{CATALOGUE_ID}/items")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total_items"] == 1

    # Delete
    response = await client.delete(f"/register/{workflow_json['id']}", headers=AUTH_HEADER)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deleted
    response = await client.get(f"/collections/{CATALOGUE_ID}/items/{workflow_json['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
