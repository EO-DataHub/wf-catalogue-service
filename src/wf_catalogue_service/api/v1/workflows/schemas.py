"""Workflow API schemas following OGC API Records standard."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from wf_catalogue_service.api.common.schemas import FilterParams, PaginationParams


class LinkSchema(BaseModel):
    """OGC Link schema."""

    model_config = ConfigDict(populate_by_name=True)

    href: str
    rel: str
    type: str | None = None
    title: str | None = None
    jupyter_kernel: dict[str, Any] | None = Field(default=None, alias="jupyter:kernel")


class ContactSchema(BaseModel):
    """OGC Contact schema."""

    name: str
    organization: str | None = None
    roles: list[str] = Field(default_factory=list)
    links: list[LinkSchema] = Field(default_factory=list)


class RecordProperties(BaseModel):
    """OGC Record properties for workflows and notebooks."""

    model_config = ConfigDict(populate_by_name=True)

    type: Literal["workflow", "notebook"]
    title: str
    description: str
    keywords: list[str] = Field(default_factory=list)
    language: str | None = None
    license: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    applicable_collections: list[str] = Field(default_factory=list, alias="applicableCollections")
    contacts: list[ContactSchema] = Field(default_factory=list)
    input_parameters: dict[str, Any] | None = Field(default=None, alias="inputParameters")
    application_type: str | None = Field(default=None, alias="application:type")
    application_container: bool | None = Field(default=None, alias="application:container")
    application_language: str | None = Field(default=None, alias="application:language")
    extent: dict[str, Any] | None = None
    # Notebook-specific fields
    jupyter_kernel_info: dict[str, Any] | None = Field(default=None, alias="jupyter_kernel_info")
    formats: list[dict[str, Any]] | None = None


class RecordCreate(BaseModel):
    """Input for creating/registering a workflow record (OGC Feature structure)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any] | None = None
    conforms_to: list[str] = Field(default_factory=list, alias="conformsTo")
    properties: RecordProperties
    links: list[LinkSchema] = Field(default_factory=list)


class RecordResponse(BaseModel):
    """Full workflow record response (OGC Feature structure)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any] | None = None
    conforms_to: list[str] = Field(default_factory=list, alias="conformsTo")
    properties: RecordProperties
    links: list[LinkSchema] = Field(default_factory=list)


class RecordSummary(BaseModel):
    """Workflow summary for list responses."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: Literal["Feature"] = "Feature"
    properties: RecordProperties


class RecordFilterRequest(PaginationParams, FilterParams):
    """Record filter params matching OGC query parameters."""

    model_config = ConfigDict(populate_by_name=True)

    q: str | None = Field(default=None, description="Free text search")
    type: Literal["workflow", "notebook"] | None = Field(default=None, description="Record type filter")
    applicable_collections: str | None = Field(default=None, alias="applicableCollections")
    keywords: str | None = None


class ConceptSchema(BaseModel):
    """Theme concept schema."""

    id: str
    title: str


class ThemeSchema(BaseModel):
    """Catalogue theme schema."""

    scheme: str | None = None
    concepts: list[ConceptSchema] = Field(default_factory=list)


class CatalogueSummary(BaseModel):
    """Catalogue summary for list responses."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: Literal["Collection"] = "Collection"
    title: str
    description: str


class CatalogueResponse(BaseModel):
    """OGC Collection response for catalogue metadata."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: Literal["Collection"] = "Collection"
    item_type: Literal["record"] = Field(default="record", alias="itemType")
    conforms_to: list[str] = Field(default_factory=list, alias="conformsTo")
    title: str
    description: str
    keywords: list[str] = Field(default_factory=list)
    themes: list[ThemeSchema] = Field(default_factory=list)
    language: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    contacts: list[ContactSchema] = Field(default_factory=list)
    license: str | None = None
    links: list[LinkSchema] = Field(default_factory=list)
