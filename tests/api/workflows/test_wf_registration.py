"""Unit tests for workflow registration endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import status

if TYPE_CHECKING:
    from starlette.testclient import TestClient


def test_register_workflow_returns_201(client: TestClient, auth_token_module_scoped: str) -> None:
    """Test that register workflow endpoint returns 201 status code."""
    payload = {
        "name": "test-workflow",
        "description": "Test workflow description",
    }
    response = client.post(
        "/api/v1.0/workflows",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token_module_scoped}"},
    )

    assert response.status_code == status.HTTP_201_CREATED


def test_register_workflow_returns_workflow_details_model(client: TestClient, auth_token_module_scoped: str) -> None:
    """Test that register workflow returns WorkflowDetails structure."""
    payload = {
        "name": "my-workflow",
        "description": "My workflow description",
    }
    response = client.post(
        "/api/v1.0/workflows",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token_module_scoped}"},
    )
    data: dict[str, Any] = response.json()

    # Verify WorkflowDetails structure
    assert "id" in data
    assert "name" in data
    assert "description" in data

    assert isinstance(data["id"], str)
    assert isinstance(data["name"], str)
    assert data["description"] is None or isinstance(data["description"], str)


def test_register_workflow_with_name_only(client: TestClient, auth_token_module_scoped: str) -> None:
    """Test registering workflow with only required name field."""
    payload = {
        "name": "minimal-workflow",
    }
    response = client.post(
        "/api/v1.0/workflows",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token_module_scoped}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data: dict[str, Any] = response.json()
    assert data["name"] == "minimal-workflow"


def test_register_workflow_returns_provided_data(client: TestClient, auth_token_module_scoped: str) -> None:
    """Test that returned workflow contains the provided data."""
    payload = {
        "name": "custom-workflow",
        "description": "Custom description",
    }
    response = client.post(
        "/api/v1.0/workflows",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token_module_scoped}"},
    )
    data: dict[str, Any] = response.json()

    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]


def test_register_workflow_without_auth_returns_403(client: TestClient) -> None:
    """Test that register workflow without authentication returns 403."""
    payload = {
        "name": "test-workflow",
        "description": "Test workflow description",
    }
    response = client.post("/api/v1.0/workflows", json=payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_register_workflow_missing_required_field_returns_422(
    client: TestClient,
    auth_token_module_scoped: str,
) -> None:
    """Test that register workflow without required name field returns 422."""
    payload: dict[str, Any] = {
        "description": "Description without name",
    }
    response = client.post(
        "/api/v1.0/workflows",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token_module_scoped}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
