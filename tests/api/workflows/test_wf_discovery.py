"""Unit tests for workflow endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import status

if TYPE_CHECKING:
    from starlette.testclient import TestClient


def test_get_workflows_returns_200(client: TestClient) -> None:
    """Test that get workflows endpoint returns 200 status code."""
    response = client.get("/api/v1.0/workflows")

    assert response.status_code == status.HTTP_200_OK


def test_get_workflows_returns_paged_response(client: TestClient) -> None:
    """Test that get workflows returns PagedResponse structure."""
    response = client.get("/api/v1.0/workflows")
    data = response.json()

    # Verify PagedResponse structure
    assert "items" in data
    assert "total_items" in data
    assert "page" in data
    assert "total_pages" in data
    assert "page_size" in data

    assert isinstance(data["items"], list)
    assert isinstance(data["total_items"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["total_pages"], int)
    assert isinstance(data["page_size"], int)


def test_get_workflows_items_have_workflow_summary_structure(client: TestClient) -> None:
    """Test that workflow items have WorkflowSummary structure."""
    response = client.get("/api/v1.0/workflows")
    data = response.json()

    if data["items"]:  # If there are items
        item = data["items"][0]
        assert "id" in item
        assert "name" in item
        assert isinstance(item["id"], str)
        assert isinstance(item["name"], str)


def test_get_workflow_details_returns_200(client: TestClient) -> None:
    """Test that get workflow details endpoint returns 200 status code."""
    workflow_id = "test-workflow-123"
    response = client.get(f"/api/v1.0/workflows/{workflow_id}")

    assert response.status_code == status.HTTP_200_OK


def test_get_workflow_details_returns_workflow_details_model(client: TestClient) -> None:
    """Test that get workflow details returns WorkflowDetails structure."""
    workflow_id = "test-workflow-456"
    response = client.get(f"/api/v1.0/workflows/{workflow_id}")
    data = response.json()

    # Verify WorkflowDetails structure
    assert "id" in data
    assert "name" in data
    assert "description" in data

    assert isinstance(data["id"], str)
    assert isinstance(data["name"], str)
    assert data["description"] is None or isinstance(data["description"], str)


def test_get_workflow_details_returns_correct_id(client: TestClient) -> None:
    """Test that returned workflow has the requested ID."""
    workflow_id = "my-custom-id"
    response = client.get(f"/api/v1.0/workflows/{workflow_id}")
    data = response.json()

    assert data["id"] == workflow_id
