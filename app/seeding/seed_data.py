from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.config import get_settings
from app.generators.factory import RealisticGenerator
from app.models.edge import Edge, EdgeState
from app.models.enterprise import Enterprise
from app.models.link import Link, LinkState
from app.state import load_state, save_state
from app.store.relationships import get_store

if TYPE_CHECKING:
    from app.store.relationships import DataStore

log = logging.getLogger("vco-sim.seed")


def seed_enterprises(
    store: DataStore,
    count: int,
    persisted_ids: list[str] | None = None
) -> list[Enterprise]:
    """Seed enterprise entities, using persisted IDs when available."""
    enterprises = []

    for i in range(count):
        # Use persisted ID if available, otherwise let model generate
        kwargs = {
            "name": RealisticGenerator.enterprise_name(),
            "network_id": 1,
            "alerts_enabled": True,
        }
        if persisted_ids and i < len(persisted_ids):
            kwargs["logical_id"] = persisted_ids[i]

        ent = Enterprise(**kwargs)
        store.enterprises.create(ent)
        enterprises.append(ent)
        log.debug("Created enterprise: %s (%s)", ent.name, ent.logical_id)

    return enterprises


def seed_edges(
    store: DataStore,
    enterprise: Enterprise,
    count: int
) -> list[Edge]:
    """Seed edge entities for an enterprise."""
    edges = []

    # Distribution of edge states
    states = [EdgeState.CONNECTED] * int(count * 0.7)
    states += [EdgeState.DEGRADED] * int(count * 0.2)
    states += [EdgeState.OFFLINE] * (count - len(states))

    for i, state in enumerate(states):
        location = RealisticGenerator.location()

        edge = Edge(
            name=RealisticGenerator.edge_name(location["city"]),
            enterprise_id=enterprise.id,
            enterprise_logical_id=enterprise.logical_id,
            edge_state=state,
            model_number=RealisticGenerator.edge_model(),
            serial_number=RealisticGenerator.serial_number(),
            site_name=f"{location['city']} Office",
            city=location["city"],
            state=location["state"],
            country=location["country"],
            postal_code=location["postal_code"],
            latitude=location["latitude"],
            longitude=location["longitude"],
        )
        store.edges.create(edge)
        edges.append(edge)
        log.debug("Created edge: %s (%s) [%s]", edge.name, edge.logical_id, state.value)

    return edges


def seed_links(store: DataStore, edge: Edge, count: int) -> list[Link]:
    """Seed WAN link entities for an edge."""
    links = []
    interfaces = ["GE1", "GE2", "GE3", "GE4", "LTE1", "WLAN1"]

    for i in range(min(count, len(interfaces))):
        # First link is primary (stable), others vary
        is_primary = i == 0
        edge_state = edge.edge_state
        healthy = (edge_state.value if hasattr(edge_state, 'value') else edge_state) == "CONNECTED"

        link = Link(
            edge_id=edge.id,
            edge_logical_id=edge.logical_id,
            enterprise_logical_id=edge.enterprise_logical_id,
            name=f"{edge.site_name or edge.name} - {interfaces[i]}",
            interface=interfaces[i],
            link_state=LinkState.STABLE if (is_primary and healthy) else LinkState.STANDBY,
            ip_address=RealisticGenerator.ip_address(public=True),
            isp=RealisticGenerator.isp(),
            upstream_mbps=RealisticGenerator.bandwidth_mbps(),
            downstream_mbps=RealisticGenerator.bandwidth_mbps(),
            latency_ms=RealisticGenerator.latency_ms(healthy),
            jitter_ms=RealisticGenerator.jitter_ms(healthy),
            loss_pct=RealisticGenerator.loss_pct(healthy),
        )
        store.links.create(link)
        links.append(link)
        log.debug("Created link: %s (%s)", link.name, link.logical_id)

    return links


def seed_all() -> None:
    """Seed all data based on configuration."""
    settings = get_settings()
    store = get_store()

    # Load persisted state
    state = load_state(settings.state_file_path)

    log.info(
        "Seeding data: %d enterprises, %d edges each, %d links each",
        settings.seed_enterprises,
        settings.seed_edges_per_enterprise,
        settings.seed_links_per_edge,
    )

    enterprises = seed_enterprises(
        store,
        settings.seed_enterprises,
        persisted_ids=state.enterprise_logical_ids
    )

    for ent in enterprises:
        edges = seed_edges(store, ent, settings.seed_edges_per_enterprise)
        for edge in edges:
            seed_links(store, edge, settings.seed_links_per_edge)

    # Save updated state (capture any new enterprise IDs)
    state.enterprise_logical_ids = [e.logical_id for e in enterprises]
    save_state(settings.state_file_path, state)

    log.info(
        "Seeding complete: %d enterprises, %d edges, %d links",
        store.enterprises.count(),
        store.edges.count(),
        store.links.count(),
    )
