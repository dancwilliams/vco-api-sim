from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel

log = logging.getLogger("vco-sim.state")


class PersistedState(BaseModel):
    """Persisted state between runs."""
    enterprise_logical_ids: list[str] = []
    # Maps enterprise_logical_id -> list of edge logical IDs (in order)
    edge_logical_ids: dict[str, list[str]] = {}


def load_state(path: Path) -> PersistedState:
    """Load state from file, or return empty state if not found."""
    if not path.exists():
        log.info("No state file found at %s, starting fresh", path)
        return PersistedState()

    try:
        with open(path) as f:
            data = json.load(f)
        state = PersistedState.model_validate(data)
        edge_count = sum(len(edges) for edges in state.edge_logical_ids.values())
        log.info("Loaded state: %d enterprise IDs, %d edge IDs", len(state.enterprise_logical_ids), edge_count)
        return state
    except Exception as e:
        log.warning("Failed to load state from %s: %s, starting fresh", path, e)
        return PersistedState()


def save_state(path: Path, state: PersistedState) -> None:
    """Save state to file."""
    try:
        with open(path, "w") as f:
            json.dump(state.model_dump(), f, indent=2)
        edge_count = sum(len(edges) for edges in state.edge_logical_ids.values())
        log.info("Saved state: %d enterprise IDs, %d edge IDs to %s", len(state.enterprise_logical_ids), edge_count, path)
    except Exception as e:
        log.error("Failed to save state to %s: %s", path, e)
