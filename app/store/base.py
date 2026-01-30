from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseStore(ABC, Generic[T]):
    """Abstract interface for entity storage."""

    @abstractmethod
    def get(self, logical_id: str) -> Optional[T]:
        """Get entity by logical ID."""
        ...

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by numeric ID."""
        ...

    @abstractmethod
    def list(self, **filters) -> List[T]:
        """List entities with optional filters."""
        ...

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity."""
        ...

    @abstractmethod
    def update(self, logical_id: str, data: dict[str, Any]) -> Optional[T]:
        """Update entity by logical ID."""
        ...

    @abstractmethod
    def delete(self, logical_id: str) -> bool:
        """Delete entity by logical ID."""
        ...
