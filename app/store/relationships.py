from __future__ import annotations

from typing import TYPE_CHECKING

from .memory import MemoryStore

if TYPE_CHECKING:
    from app.models.enterprise import Enterprise
    from app.models.edge import Edge
    from app.models.link import Link


class DataStore:
    """Central data store managing all entity types and relationships."""

    def __init__(self) -> None:
        self.enterprises: MemoryStore[Enterprise] = MemoryStore()
        self.edges: MemoryStore[Edge] = MemoryStore()
        self.links: MemoryStore[Link] = MemoryStore()

        # Set up indexes for common queries
        self.edges.add_index("enterprise_logical_id")
        self.links.add_index("edge_logical_id")
        self.links.add_index("enterprise_logical_id")

    def get_enterprise_edges(self, enterprise_logical_id: str) -> list:
        """Get all edges for an enterprise."""
        return self.edges.list(enterprise_logical_id=enterprise_logical_id)

    def get_edge_links(self, edge_logical_id: str) -> list:
        """Get all links for an edge."""
        return self.links.list(edge_logical_id=edge_logical_id)

    def delete_enterprise_cascade(self, enterprise_logical_id: str) -> bool:
        """Delete enterprise and all related entities."""
        # Delete all links for this enterprise's edges
        edges = self.get_enterprise_edges(enterprise_logical_id)
        for edge in edges:
            links = self.get_edge_links(edge.logical_id)
            for link in links:
                self.links.delete(link.logical_id)
            self.edges.delete(edge.logical_id)

        return self.enterprises.delete(enterprise_logical_id)


# Global singleton
_store: DataStore | None = None


def get_store() -> DataStore:
    """Get or create the global data store."""
    global _store
    if _store is None:
        _store = DataStore()
    return _store


def reset_store() -> None:
    """Reset the global data store (for testing)."""
    global _store
    _store = None
