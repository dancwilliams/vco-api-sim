from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


def _resolve_spec_path(path: str | os.PathLike[str] | None = None) -> Path:
    candidate = path or os.getenv("VCO_SPEC_PATH")
    if candidate:
        return Path(candidate)

    # Fallback: look for a local spec in common locations to reduce setup friction.
    repo_root = Path(__file__).resolve().parents[1]
    candidates = [
        repo_root / "vco-api-json" / "vco_api.json",
        repo_root / "vco-api-json" / "vco_api",
    ]
    for guess in candidates:
        if guess.exists() and guess.is_file():
            return guess

    raise FileNotFoundError(
        "OpenAPI spec not provided. Set VCO_SPEC_PATH to the VCO OpenAPI JSON file before starting the simulator."
    )


def load_spec(path: str | os.PathLike[str] | None = None) -> Dict[str, Any]:
    spec_path = _resolve_spec_path(path)
    if not spec_path.exists() or not spec_path.is_file():
        raise FileNotFoundError(f"Unable to find OpenAPI file at {spec_path}")
    with spec_path.open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def cached_spec(path: str | os.PathLike[str] | None = None) -> Dict[str, Any]:
    return load_spec(path)
