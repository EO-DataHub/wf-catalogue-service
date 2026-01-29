"""OGC API Records compliant routes."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from wf_catalogue_service.api.auth.helpers import validate_access_token
from wf_catalogue_service.api.common.schemas import PagedResponse
from wf_catalogue_service.api.v1.workflows.schemas import (
    CatalogueResponse,
    CatalogueSummary,
    ConceptSchema,
    ContactSchema,
    LinkSchema,
    RecordCreate,
    RecordFilterRequest,
    RecordProperties,
    RecordResponse,
    RecordSummary,
    ThemeSchema,
)
from wf_catalogue_service.db.models import Catalogue, Contact, Link, Record, RecordType, Theme
from wf_catalogue_service.db.session import get_session

workflow_router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
)


def _db_record_to_response(record: Record, contacts: list[Contact], links: list[Link]) -> RecordResponse:
    """Convert database record to OGC Record response."""
    return RecordResponse(
        id=record.id,
        type="Feature",
        geometry=record.geometry,
        conforms_to=record.conforms_to or [],
        properties=RecordProperties(
            type=record.type.value,
            title=record.title,
            description=record.description,
            keywords=record.keywords,
            language=record.language,
            license=record.license,
            created=record.created,
            updated=record.updated,
            applicable_collections=record.applicable_collections,
            contacts=[
                ContactSchema(
                    name=c.name,
                    organization=c.organization,
                    roles=c.roles,
                    links=[],
                )
                for c in contacts
            ],
            input_parameters=record.input_parameters,
            application_type=record.application_type,
            application_container=record.application_container,
            application_language=record.application_language,
            extent=record.extent,
            jupyter_kernel_info=record.jupyter_kernel_info,
            formats=record.formats,
        ),
        links=[
            LinkSchema(
                href=link.href,
                rel=link.rel,
                type=link.type,
                title=link.title,
                jupyter_kernel=link.jupyter_kernel,
            )
            for link in links
        ],
    )


DEFAULT_CATALOGUE_ID = "eodh-workflows-notebooks"


def _db_record_to_summary(record: Record) -> RecordSummary:
    """Convert database record to summary response."""
    return RecordSummary(
        id=record.id,
        type="Feature",
        properties=RecordProperties(
            type=record.type.value,
            title=record.title,
            description=record.description,
            keywords=record.keywords,
            language=record.language,
            license=record.license,
            created=record.created,
            updated=record.updated,
            applicable_collections=record.applicable_collections,
            contacts=[],
            input_parameters=record.input_parameters,
            application_type=record.application_type,
            application_container=record.application_container,
            application_language=record.application_language,
            extent=record.extent,
            jupyter_kernel_info=record.jupyter_kernel_info,
            formats=record.formats,
        ),
    )


@workflow_router.get("")
async def get_collections(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CatalogueSummary]:
    """List all catalogues."""
    result = await session.execute(select(Catalogue))
    catalogues = result.scalars().all()
    return [
        CatalogueSummary(
            id=cat.id,
            type="Collection",
            title=cat.title,
            description=cat.description,
        )
        for cat in catalogues
    ]


@workflow_router.get("/{catalogue_id}/items")
async def get_items(
    catalogue_id: str,
    query: Annotated[RecordFilterRequest, Query()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PagedResponse[RecordSummary]:
    """List records in a catalogue (OGC API Records compliant)."""
    select_query = select(Record).where(Record.catalogue_id == catalogue_id)

    # Filter by type
    if query.type:
        select_query = select_query.where(Record.type == RecordType(query.type))

    # Free text search
    if query.q:
        search = f"%{query.q}%"
        select_query = select_query.where(Record.title.ilike(search) | Record.description.ilike(search))

    # Filter by applicable collection
    if query.applicable_collections:
        select_query = select_query.where(Record.applicable_collections.contains([query.applicable_collections]))

    # Filter by keyword
    if query.keywords:
        select_query = select_query.where(Record.keywords.contains([query.keywords]))

    total_items = await session.scalar(select(func.count()).select_from(select_query.subquery())) or 0

    # Ordering
    if query.order_by:
        order_col = getattr(Record, query.order_by, Record.created)
        select_query = select_query.order_by(order_col.desc() if query.order_direction == "desc" else order_col.asc())
    else:
        select_query = select_query.order_by(Record.created.desc())

    # Pagination
    select_query = select_query.offset((query.page - 1) * query.page_size).limit(query.page_size)
    result = await session.execute(select_query)
    records = result.scalars().all()

    total_pages = (total_items + query.page_size - 1) // query.page_size

    return PagedResponse(
        items=[_db_record_to_summary(record) for record in records],
        total_items=total_items,
        page=query.page,
        total_pages=total_pages,
        page_size=query.page_size,
    )


@workflow_router.get("/{catalogue_id}/items/{record_id}")
async def get_item(
    catalogue_id: str,
    record_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RecordResponse:
    """Get a single record by ID (OGC API Records compliant)."""
    # Get record
    select_query = select(Record).where(Record.id == record_id, Record.catalogue_id == catalogue_id)
    result = await session.execute(select_query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Record not found")

    # Get contacts for this record
    contacts_query = select(Contact).where(Contact.entity_id == record_id, Contact.entity_type == "record")
    contacts_result = await session.execute(contacts_query)
    contacts = list(contacts_result.scalars().all())

    # Get links for this record
    links_query = select(Link).where(Link.entity_id == record_id, Link.entity_type == "record")
    links_result = await session.execute(links_query)
    links = list(links_result.scalars().all())

    return _db_record_to_response(record, contacts, links)


@workflow_router.get("/{catalogue_id}")
async def get_catalogue(
    catalogue_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CatalogueResponse:
    """Get catalogue metadata (OGC API Records compliant)."""
    query = (
        select(Catalogue)
        .options(selectinload(Catalogue.themes).selectinload(Theme.concepts))
        .where(Catalogue.id == catalogue_id)
    )
    result = await session.execute(query)
    catalogue = result.scalar_one_or_none()

    if not catalogue:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Catalogue not found")

    # Contacts and links (polymorphic - no relationships)
    contacts_query = select(Contact).where(Contact.entity_id == catalogue_id, Contact.entity_type == "catalogue")
    contacts_result = await session.execute(contacts_query)
    contacts = list(contacts_result.scalars().all())

    links_query = select(Link).where(Link.entity_id == catalogue_id, Link.entity_type == "catalogue")
    links_result = await session.execute(links_query)
    links = list(links_result.scalars().all())

    return CatalogueResponse(
        id=catalogue.id,
        type="Collection",
        item_type=catalogue.item_type,
        conforms_to=catalogue.conforms_to or [],
        title=catalogue.title,
        description=catalogue.description,
        keywords=catalogue.keywords,
        themes=[
            ThemeSchema(
                scheme=theme.scheme,
                concepts=[ConceptSchema(id=c.concept_id, title=c.title) for c in theme.concepts],
            )
            for theme in catalogue.themes
        ],
        language=catalogue.language,
        created=catalogue.created,
        updated=catalogue.updated,
        contacts=[ContactSchema(name=c.name, organization=c.organization, roles=c.roles, links=[]) for c in contacts],
        license=catalogue.license,
        links=[LinkSchema(href=link.href, rel=link.rel, type=link.type, title=link.title) for link in links],
    )


# Registration router
register_router = APIRouter(tags=["Registration"])


@register_router.post("/register", response_model=RecordResponse, status_code=HTTPStatus.CREATED)
async def register_record(
    data: RecordCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    credential: Annotated[HTTPAuthorizationCredentials, Depends(validate_access_token)],  # noqa: ARG001
) -> RecordResponse:
    """Register a new workflow/notebook record."""
    # Check for existing record
    existing = await session.get(Record, data.id)
    if existing:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="Record with this ID already exists")

    # Determine record type from properties
    record_type = RecordType(data.properties.type)

    # Create record (auto-assign to default catalogue)
    record = Record(
        id=data.id,
        catalogue_id=DEFAULT_CATALOGUE_ID,
        type=record_type,
        geometry=data.geometry,
        conforms_to=data.conforms_to,
        title=data.properties.title,
        description=data.properties.description,
        keywords=data.properties.keywords,
        language=data.properties.language,
        license=data.properties.license,
        applicable_collections=data.properties.applicable_collections,
        input_parameters=data.properties.input_parameters,
        application_type=data.properties.application_type,
        application_container=data.properties.application_container,
        application_language=data.properties.application_language,
        extent=data.properties.extent,
        jupyter_kernel_info=data.properties.jupyter_kernel_info,
        formats=data.properties.formats,
    )
    session.add(record)

    # Create contacts
    contacts = []
    for contact_data in data.properties.contacts:
        contact = Contact(
            id=str(uuid.uuid4()),
            entity_id=record.id,
            entity_type="record",
            name=contact_data.name,
            organization=contact_data.organization,
            roles=contact_data.roles,
        )
        session.add(contact)
        contacts.append(contact)

    # Create links
    links = []
    for link_data in data.links:
        link = Link(
            entity_id=record.id,
            entity_type="record",
            href=link_data.href,
            rel=link_data.rel,
            type=link_data.type,
            title=link_data.title,
            jupyter_kernel=link_data.jupyter_kernel,
        )
        session.add(link)
        links.append(link)

    await session.commit()
    await session.refresh(record)

    return _db_record_to_response(record, contacts, links)


@register_router.delete("/register/{record_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_record(
    record_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    credential: Annotated[HTTPAuthorizationCredentials, Depends(validate_access_token)],  # noqa: ARG001
) -> None:
    """Delete a workflow/notebook record."""
    record = await session.get(Record, record_id)
    if not record:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Record not found")

    await session.execute(delete(Contact).where(Contact.entity_id == record_id, Contact.entity_type == "record"))
    await session.execute(delete(Link).where(Link.entity_id == record_id, Link.entity_type == "record"))
    await session.delete(record)
    await session.commit()
