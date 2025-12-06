from __future__ import annotations

from typing import Any, Dict, Iterable


class SchemaResolver:
    """Helper to resolve $ref pointers within the loaded OpenAPI document."""

    def __init__(self, spec: Dict[str, Any]) -> None:
        self.spec = spec
        self.components = spec.get("components", {})

    def resolve(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        if "$ref" in schema:
            return self._follow(schema["$ref"])
        return schema

    def _follow(self, ref: str) -> Dict[str, Any]:
        target = ref.lstrip("#/").split("/")
        node: Any = self.spec
        for part in target:
            node = node[part]
        if not isinstance(node, dict):
            raise ValueError(f"Reference {ref} did not resolve to an object")
        return node


def _pick_priority_schema(
    options: Iterable[Dict[str, Any]], resolver: SchemaResolver, depth: int
) -> Any:
    for candidate in options:
        resolved = resolver.resolve(candidate)
        value = example_from_schema(resolved, resolver, depth + 1)
        if value is not None:
            return value
    return None


def example_from_schema(
    schema: Dict[str, Any] | None, resolver: SchemaResolver, depth: int = 0
) -> Any:
    """Generate a lightweight example payload from a JSON schema."""
    if schema is None:
        return None
    if depth > 8:
        return None

    schema = resolver.resolve(schema)

    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if "enum" in schema:
        return schema["enum"][0]

    if "oneOf" in schema:
        return _pick_priority_schema(schema["oneOf"], resolver, depth)
    if "anyOf" in schema:
        return _pick_priority_schema(schema["anyOf"], resolver, depth)
    if "allOf" in schema:
        merged: Dict[str, Any] = {}
        for part in schema["allOf"]:
            resolved = resolver.resolve(part)
            value = example_from_schema(resolved, resolver, depth + 1)
            if isinstance(value, dict):
                merged.update(value)
        return merged or None

    type_hint = schema.get("type")
    fmt = schema.get("format")

    if type_hint == "object":
        props = schema.get("properties", {})
        out: Dict[str, Any] = {}
        for name, subschema in props.items():
            out[name] = example_from_schema(subschema, resolver, depth + 1)
        if not out and schema.get("additionalProperties") is True:
            out["key"] = "value"
        elif isinstance(schema.get("additionalProperties"), dict):
            out["key"] = example_from_schema(
                schema["additionalProperties"], resolver, depth + 1
            )
        return out

    if type_hint == "array":
        item_schema = schema.get("items", {})
        return [example_from_schema(item_schema, resolver, depth + 1)]

    if type_hint == "integer":
        return 0
    if type_hint == "number":
        return 0.0
    if type_hint == "boolean":
        return True
    if type_hint == "string":
        if fmt in {"date-time", "datetime"}:
            return "2024-01-01T00:00:00Z"
        if fmt == "date":
            return "2024-01-01"
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        if fmt in {"email", "idn-email"}:
            return "user@example.com"
        if fmt == "hostname":
            return "edge.local"
        if fmt == "ipv4":
            return "192.0.2.1"
        if fmt == "ipv6":
            return "2001:db8::1"
        if fmt == "uri":
            return "https://example.com"
        return "string"

    if type_hint is None and "$ref" in schema:
        return example_from_schema(schema, resolver, depth + 1)

    return None

