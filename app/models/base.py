from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


def generate_logical_id() -> str:
    """Generate a UUID-style logical ID."""
    return str(uuid.uuid4())


def generate_timestamp() -> datetime:
    """Generate current UTC timestamp."""
    return datetime.utcnow()


class VCOBaseModel(BaseModel):
    """Base model for all VCO entities."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra="allow",
    )

    id: int = Field(default_factory=lambda: int(uuid.uuid4().int % 2**31))
    logical_id: str = Field(default_factory=generate_logical_id, alias="logicalId")
    created: datetime = Field(default_factory=generate_timestamp)
    modified: Optional[datetime] = Field(default=None)


class MinMaxAverage(BaseModel):
    """Common pattern for metric aggregates."""
    min: float = 0.0
    max: float = 0.0
    average: float = 0.0


class HrefMixin:
    """Mixin for API resources with _href. Use with BaseModel classes."""
    href: Optional[str] = Field(default=None, alias="_href")


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""
    data: list[Any] = Field(default_factory=list)
    meta_data: dict[str, Any] = Field(
        default_factory=lambda: {"more": False, "nextPageLink": None},
        alias="metaData"
    )
