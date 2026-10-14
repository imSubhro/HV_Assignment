import math
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")


def ensure_utc(value: Any) -> Any:
    """Accept naive datetimes as UTC, mirroring the ISO-8601 UTC convention."""
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total_items: int
    total_pages: int


def paginate(items: list[T], *, page: int, page_size: int, total_items: int) -> Page[T]:
    return Page[T](
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=math.ceil(total_items / page_size) if total_items else 0,
    )


class PaginationParams:
    """Reusable `page` / `page_size` query-parameter dependency."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number, 1-based"),
        page_size: int = Query(10, ge=1, le=50, description="Items per page (1-50)"),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Message(BaseModel):
    detail: str = Field(description="Human-readable message")


__all__ = ["Message", "Page", "PaginationParams", "paginate"]
