"""Workflow API schemas."""

from __future__ import annotations

from pydantic import BaseModel

from wf_catalogue_service.api.common.schemas import FilterParams, PaginationParams


class WorkflowRegistrationRequest(BaseModel):
    """Workflow registration request."""

    name: str
    description: str | None = None


class WorkflowSummary(BaseModel):
    """Workflow summary."""

    id: str
    name: str


class WorkflowDetails(WorkflowSummary):
    """Workflow details."""

    id: str
    name: str
    description: str | None = None


class WorkflowFilterRequest(PaginationParams, FilterParams):
    """Workflow filter params."""

    query: str | None = None
