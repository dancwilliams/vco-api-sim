from __future__ import annotations

from typing import Any, Dict


class SchemaResolver:
    """Resolve $ref pointers in OpenAPI specs."""

    def __init__(self, spec: Dict[str, Any]) -> None:
        self.spec = spec
        self._cache: Dict[str, Dict[str, Any]] = {}

    def resolve(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a schema, following $ref if present."""
        if "$ref" not in schema:
            return schema

        ref = schema["$ref"]
        if ref in self._cache:
            return self._cache[ref]

        resolved = self._follow_ref(ref)
        self._cache[ref] = resolved
        return resolved

    def _follow_ref(self, ref: str) -> Dict[str, Any]:
        """Follow a $ref pointer to its target."""
        parts = ref.lstrip("#/").split("/")
        node: Any = self.spec

        for part in parts:
            # Handle URL-encoded characters
            part = part.replace("~1", "/").replace("~0", "~")
            if isinstance(node, dict):
                node = node.get(part)
            else:
                raise ValueError(f"Cannot resolve {ref}: {part} not found")

        if not isinstance(node, dict):
            raise ValueError(f"Reference {ref} did not resolve to an object")

        return node

    def get_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get all schema definitions."""
        # Swagger 2.0
        if "definitions" in self.spec:
            return self.spec["definitions"]
        # OpenAPI 3.0
        if "components" in self.spec:
            return self.spec.get("components", {}).get("schemas", {})
        return {}
