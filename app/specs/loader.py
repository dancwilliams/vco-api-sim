from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.config import get_settings


def load_spec(path: Path) -> Dict[str, Any]:
    """Load a single OpenAPI spec from disk."""
    if not path.exists():
        raise FileNotFoundError(f"Spec not found: {path}")

    with path.open(encoding="utf-8") as f:
        return json.load(f)


def detect_version(spec: Dict[str, Any]) -> str:
    """Detect OpenAPI version from spec."""
    if "swagger" in spec:
        return "2.0"
    if "openapi" in spec:
        return spec["openapi"]
    return "unknown"


@lru_cache(maxsize=1)
def load_specs() -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Load both V1 and V2 specs."""
    settings = get_settings()
    v1_path, v2_path = settings.resolve_specs()

    v1_spec = None
    v2_spec = None

    if v1_path and v1_path.exists():
        v1_spec = load_spec(v1_path)

    if v2_path and v2_path.exists():
        v2_spec = load_spec(v2_path)

    return v1_spec, v2_spec


def get_v1_spec() -> Optional[Dict[str, Any]]:
    """Get V1 spec."""
    v1, _ = load_specs()
    return v1


def get_v2_spec() -> Optional[Dict[str, Any]]:
    """Get V2 spec."""
    _, v2 = load_specs()
    return v2
