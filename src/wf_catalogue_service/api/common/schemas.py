"""Shared schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class PaginationParams(BaseModel):
    """Pagination params."""

    page: int = 1
    page_size: int = 10


class OrderDirection(StrEnum):
    """Enum representing ordering direction."""

    asc = "asc"
    desc = "desc"


class FilterParams(BaseModel):
    """Filter params."""

    order_by: str | None = None
    order_direction: OrderDirection = OrderDirection.asc


class PagedResponse[T](BaseModel):
    """Response with pagination."""

    items: list[T]
    total_items: int
    page: int
    total_pages: int
    page_size: int = 10
