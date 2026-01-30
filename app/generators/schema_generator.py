from __future__ import annotations

from typing import Any, Dict, Optional

from .factory import RealisticGenerator


class SchemaGenerator:
    """Generate data based on OpenAPI schema definitions."""

    def __init__(self, spec: Dict[str, Any]) -> None:
        self.spec = spec
        self._definitions = spec.get("definitions", {})
        self._components = spec.get("components", {}).get("schemas", {})

    def _resolve_ref(self, ref: str) -> Dict[str, Any]:
        """Resolve a $ref pointer."""
        parts = ref.lstrip("#/").split("/")
        node = self.spec
        for part in parts:
            node = node[part]
        return node

    def generate(self, schema: Dict[str, Any], depth: int = 0) -> Any:
        """Generate value from schema."""
        if depth > 10:
            return None

        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])

        # Check for example/default first
        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]
        if "enum" in schema:
            return schema["enum"][0]

        # Handle composition
        if "oneOf" in schema:
            return self.generate(schema["oneOf"][0], depth + 1)
        if "anyOf" in schema:
            return self.generate(schema["anyOf"][0], depth + 1)
        if "allOf" in schema:
            result = {}
            for part in schema["allOf"]:
                val = self.generate(part, depth + 1)
                if isinstance(val, dict):
                    result.update(val)
            return result

        type_hint = schema.get("type")
        format_hint = schema.get("format")

        # Use realistic generators for known patterns
        if type_hint == "string":
            return self._generate_string(schema, format_hint)
        if type_hint == "integer":
            return self._generate_integer(schema)
        if type_hint == "number":
            return self._generate_number(schema)
        if type_hint == "boolean":
            return True
        if type_hint == "array":
            items = schema.get("items", {})
            return [self.generate(items, depth + 1)]
        if type_hint == "object":
            return self._generate_object(schema, depth)

        return None

    def _generate_string(self, schema: Dict[str, Any], format_hint: Optional[str]) -> str:
        """Generate string value."""
        if format_hint == "date-time":
            return "2024-01-15T12:00:00Z"
        if format_hint == "date":
            return "2024-01-15"
        if format_hint == "uuid":
            return RealisticGenerator.enterprise_name()  # Use as placeholder
        if format_hint == "ipv4":
            return RealisticGenerator.ip_address()
        if format_hint == "email":
            return "admin@example.com"
        if format_hint == "hostname":
            return "edge.local"
        if format_hint == "uri":
            return "https://example.com"

        # Check property name hints
        return "string"

    def _generate_integer(self, schema: Dict[str, Any]) -> int:
        """Generate integer value."""
        min_val = schema.get("minimum", 0)
        return min_val

    def _generate_number(self, schema: Dict[str, Any]) -> float:
        """Generate number value."""
        min_val = schema.get("minimum", 0.0)
        return float(min_val)

    def _generate_object(self, schema: Dict[str, Any], depth: int) -> Dict[str, Any]:
        """Generate object value."""
        properties = schema.get("properties", {})
        result = {}

        for name, prop_schema in properties.items():
            result[name] = self.generate(prop_schema, depth + 1)

        if not result and schema.get("additionalProperties"):
            result["key"] = "value"

        return result
