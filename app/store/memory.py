from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from .base import BaseStore

T = TypeVar("T")


class MemoryStore(BaseStore[T], Generic[T]):
    """In-memory store with primary and secondary indexes."""

    def __init__(self) -> None:
        self._by_logical_id: Dict[str, T] = {}
        self._by_id: Dict[int, str] = {}  # id -> logical_id
        self._secondary_indexes: Dict[str, Dict[Any, List[str]]] = {}

    def add_index(self, field: str) -> None:
        """Add a secondary index on a field."""
        self._secondary_indexes[field] = {}

    def _index_entity(self, entity: T) -> None:
        """Add entity to secondary indexes."""
        for field, index in self._secondary_indexes.items():
            value = getattr(entity, field, None)
            if value is not None:
                if value not in index:
                    index[value] = []
                logical_id = getattr(entity, "logical_id")
                if logical_id not in index[value]:
                    index[value].append(logical_id)

    def _unindex_entity(self, entity: T) -> None:
        """Remove entity from secondary indexes."""
        for field, index in self._secondary_indexes.items():
            value = getattr(entity, field, None)
            if value is not None and value in index:
                logical_id = getattr(entity, "logical_id")
                if logical_id in index[value]:
                    index[value].remove(logical_id)

    def get(self, logical_id: str) -> Optional[T]:
        return self._by_logical_id.get(logical_id)

    def get_by_id(self, id: int) -> Optional[T]:
        logical_id = self._by_id.get(id)
        if logical_id:
            return self._by_logical_id.get(logical_id)
        return None

    def list(self, **filters) -> List[T]:
        results = list(self._by_logical_id.values())

        for field, value in filters.items():
            if field in self._secondary_indexes and value in self._secondary_indexes[field]:
                # Use index for faster lookup
                indexed_ids = self._secondary_indexes[field][value]
                results = [e for e in results if getattr(e, "logical_id") in indexed_ids]
            else:
                # Fall back to linear scan
                results = [e for e in results if getattr(e, field, None) == value]

        return results

    def create(self, entity: T) -> T:
        logical_id = getattr(entity, "logical_id")
        entity_id = getattr(entity, "id")

        self._by_logical_id[logical_id] = entity
        self._by_id[entity_id] = logical_id
        self._index_entity(entity)

        return entity

    def update(self, logical_id: str, data: dict[str, Any]) -> Optional[T]:
        entity = self._by_logical_id.get(logical_id)
        if entity is None:
            return None

        self._unindex_entity(entity)

        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        # Update modified timestamp
        if hasattr(entity, "modified"):
            setattr(entity, "modified", datetime.utcnow())

        self._index_entity(entity)
        return entity

    def delete(self, logical_id: str) -> bool:
        entity = self._by_logical_id.get(logical_id)
        if entity is None:
            return False

        self._unindex_entity(entity)
        entity_id = getattr(entity, "id")

        del self._by_logical_id[logical_id]
        if entity_id in self._by_id:
            del self._by_id[entity_id]

        return True

    def count(self) -> int:
        return len(self._by_logical_id)
