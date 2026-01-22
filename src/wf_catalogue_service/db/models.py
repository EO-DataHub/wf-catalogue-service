"""SQLAlchemy models matching Oxidian's database schema."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class RecordType(enum.Enum):
    """Record type enum."""

    workflow = "workflow"
    notebook = "notebook"


class Base(DeclarativeBase):
    """Base class for all models."""


class Catalogue(Base):
    """Catalogue model - top-level catalogue metadata."""

    __tablename__ = "catalogues"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    type: Mapped[str] = mapped_column(Text, nullable=False, default="Collection")
    item_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    language: Mapped[str | None] = mapped_column(Text)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    license: Mapped[str | None] = mapped_column(Text)
    conforms_to: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    records: Mapped[list[Record]] = relationship(back_populates="catalogue", cascade="all, delete-orphan")
    themes: Mapped[list[Theme]] = relationship(back_populates="catalogue", cascade="all, delete-orphan")


class Record(Base):
    """Record model - workflows and notebooks."""

    __tablename__ = "records"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    catalogue_id: Mapped[str | None] = mapped_column(Text, ForeignKey("catalogues.id", ondelete="CASCADE"))
    type: Mapped[RecordType] = mapped_column(Enum(RecordType, name="record_type"), nullable=False)
    geometry: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    conforms_to: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    language: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(Text)
    applicable_collections: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    # Workflow-specific
    input_parameters: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    application_type: Mapped[str | None] = mapped_column(Text)
    application_container: Mapped[bool | None] = mapped_column()
    application_language: Mapped[str | None] = mapped_column(Text)
    extent: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Notebook-specific
    jupyter_kernel_info: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    formats: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    catalogue: Mapped[Catalogue | None] = relationship(back_populates="records")

    __table_args__ = (
        Index("idx_records_catalogue", "catalogue_id"),
        Index("idx_records_type", "type"),
        Index("idx_records_keywords", "keywords", postgresql_using="gin"),
    )


class Contact(Base):
    """Contact model - contact information for entities (catalogue or record)."""

    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    organization: Mapped[str | None] = mapped_column(Text)
    roles: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    __table_args__ = (
        CheckConstraint(entity_type.in_(["catalogue", "record"]), name="ck_contacts_entity_type"),
        Index("idx_contacts_entity", "entity_id", "entity_type"),
    )


class Link(Base):
    """Link model - OGC-style cross-references (catalogue, record, or contact)."""

    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    href: Mapped[str] = mapped_column(Text, nullable=False)
    rel: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    jupyter_kernel: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        CheckConstraint(entity_type.in_(["catalogue", "record", "contact"]), name="ck_links_entity_type"),
        Index("idx_links_entity", "entity_id", "entity_type"),
    )


class Theme(Base):
    """Theme model - thematic categorization for catalogues."""

    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    catalogue_id: Mapped[str] = mapped_column(Text, ForeignKey("catalogues.id", ondelete="CASCADE"), nullable=False)
    scheme: Mapped[str | None] = mapped_column(Text)

    catalogue: Mapped[Catalogue] = relationship(back_populates="themes")
    concepts: Mapped[list[Concept]] = relationship(back_populates="theme", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_themes_catalogue", "catalogue_id"),)


class Concept(Base):
    """Concept model - individual concepts within a theme."""

    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    theme_id: Mapped[int] = mapped_column(Integer, ForeignKey("themes.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    theme: Mapped[Theme] = relationship(back_populates="concepts")
