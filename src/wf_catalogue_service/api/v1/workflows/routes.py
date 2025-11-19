"""Workflow API routes."""

from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials  # noqa: TC002

from wf_catalogue_service.api.auth.helpers import validate_access_token
from wf_catalogue_service.api.common import PagedResponse
from wf_catalogue_service.api.v1.workflows.schemas import (
    WorkflowDetails,
    WorkflowFilterRequest,
    WorkflowRegistrationRequest,
    WorkflowSummary,
)

workflow_router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"],
)


@workflow_router.get("")
async def get_workflows(query: Annotated[WorkflowFilterRequest, Query()]) -> PagedResponse[WorkflowSummary]:
    """Get workflows."""
    # TODO - dummy implementation for now - change once DB becomes available
    items = [
        WorkflowDetails(
            id="1",
            name=f"test-{i}",
            description=f"Test workflow #{i}",
        )
        for i in range(15)
    ]

    if query.query:
        search_query = query.query.lower()
        items = [
            item
            for item in items
            if search_query in item.name.lower() or (item.description and search_query in item.description.lower())
        ]

    if query.order_by:
        items = sorted(
            items,
            key=lambda item: getattr(item, query.order_by, "") or "",  # type: ignore[arg-type]
            reverse=query.order_direction == "desc",
        )

    total_items = len(items)
    total_pages = (total_items + query.page_size - 1) // query.page_size

    start = (query.page - 1) * query.page_size
    end = start + query.page_size

    return PagedResponse(
        items=items[start:end],
        total_items=total_items,
        page=query.page,
        total_pages=total_pages,
        page_size=query.page_size,
    )


@workflow_router.get("/{workflow_id}")
async def get_workflow_details(workflow_id: str) -> WorkflowDetails:
    """Get workflow details."""
    # TODO - dummy implementation for now - change once DB becomes available
    return WorkflowDetails(
        id=workflow_id,
        name=f"test-workflow-{workflow_id}",
        description=f"Test workflow #{workflow_id}",
    )


@workflow_router.post("", response_model=WorkflowDetails, status_code=HTTPStatus.CREATED)
async def register_workflow(
    data: WorkflowRegistrationRequest,
    credential: Annotated[HTTPAuthorizationCredentials, Depends(validate_access_token)],  # noqa: ARG001
) -> WorkflowDetails:
    """Register workflow."""
    # TODO - dummy implementation for now - change once DB becomes available
    return WorkflowDetails(
        id="1",
        name=data.name,
        description=data.description,
    )
