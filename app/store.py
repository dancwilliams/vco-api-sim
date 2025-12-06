from __future__ import annotations

from typing import Any, Dict, Tuple


class MemoryStore:
    """Simple in-memory store for mock resources keyed by path + params."""

    def __init__(self) -> None:
        self._data: Dict[Tuple[str, str, Tuple[Tuple[str, Any], ...]], Any] = {}

    def _key(self, path: str, method: str, path_params: Dict[str, Any]) -> Tuple[str, str, Tuple[Tuple[str, Any], ...]]:
        return (
            path,
            method.lower(),
            tuple(sorted(path_params.items())),
        )

    def get(self, path: str, method: str, path_params: Dict[str, Any]) -> Any:
        return self._data.get(self._key(path, method, path_params))

    def set(self, path: str, method: str, path_params: Dict[str, Any], payload: Any) -> None:
        self._data[self._key(path, method, path_params)] = payload

    def delete(self, path: str, method: str, path_params: Dict[str, Any]) -> None:
        self._data.pop(self._key(path, method, path_params), None)

