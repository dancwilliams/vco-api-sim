from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse

from app.generators.schema_generator import SchemaGenerator
from app.specs.resolver import SchemaResolver
from app.store.relationships import get_store

log = logging.getLogger("vco-sim.v1")


class V1Handler:
    """Handler for V1 JSON-RPC style endpoints."""

    def __init__(self, spec: Dict[str, Any]) -> None:
        self.spec = spec
        self.resolver = SchemaResolver(spec)
        self.generator = SchemaGenerator(spec)
        self.store = get_store()

    async def handle_request(
        self,
        request: Request,
        path: str,
        operation: Dict[str, Any],
    ) -> JSONResponse:
        """Handle a V1 API request."""
        body: Dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            pass

        log.debug("V1 request: %s body=%s", path, body)

        # Route to appropriate handler based on path pattern
        if path.startswith("/login/"):
            return self._handle_login(path, body)
        if path == "/logout":
            return self._handle_logout()

        # Determine operation type from path
        if "/get" in path.lower():
            return self._handle_get(path, operation, body)
        if "/insert" in path.lower() or "/create" in path.lower() or "/provision" in path.lower():
            return self._handle_create(path, operation, body)
        if "/update" in path.lower():
            return self._handle_update(path, operation, body)
        if "/delete" in path.lower():
            return self._handle_delete(path, operation, body)

        # Default: generate response from schema
        return self._generate_response(operation)

    def _handle_login(self, path: str, body: Dict[str, Any]) -> JSONResponse:
        """Handle login endpoints."""
        # Accept any credentials
        return JSONResponse(
            {"success": True},
            status_code=200,
            headers={"Set-Cookie": "velocloud.session=mock-session-token; Path=/"}
        )

    def _handle_logout(self) -> JSONResponse:
        """Handle logout."""
        return JSONResponse({"success": True})

    def _handle_get(
        self,
        path: str,
        operation: Dict[str, Any],
        body: Dict[str, Any]
    ) -> JSONResponse:
        """Handle GET-style operations."""
        enterprise_id = body.get("enterpriseId")
        edge_id = body.get("edgeId")

        # Try to serve from store first
        if "enterprise" in path.lower() and enterprise_id:
            if "edge" in path.lower():
                if edge_id:
                    # Get specific edge
                    edges = self.store.edges.list(enterprise_id=enterprise_id)
                    for e in edges:
                        if e.id == edge_id:
                            return JSONResponse(e.to_v1_dict())
                else:
                    # List edges
                    edges = self.store.edges.list(enterprise_id=enterprise_id)
                    return JSONResponse([e.to_v1_dict() for e in edges])
            else:
                # Get enterprise
                ent = self.store.enterprises.get_by_id(enterprise_id)
                if ent:
                    return JSONResponse(ent.to_v1_dict())

        # Fall back to schema-generated response
        return self._generate_response(operation)

    def _handle_create(
        self,
        path: str,
        operation: Dict[str, Any],
        body: Dict[str, Any]
    ) -> JSONResponse:
        """Handle create operations."""
        # Generate response indicating success
        response = self._generate_response(operation)
        return response

    def _handle_update(
        self,
        path: str,
        operation: Dict[str, Any],
        body: Dict[str, Any]
    ) -> JSONResponse:
        """Handle update operations."""
        return self._generate_response(operation)

    def _handle_delete(
        self,
        path: str,
        operation: Dict[str, Any],
        body: Dict[str, Any]
    ) -> JSONResponse:
        """Handle delete operations."""
        return JSONResponse({"rows": 1})

    def _generate_response(self, operation: Dict[str, Any]) -> JSONResponse:
        """Generate response from operation schema."""
        responses = operation.get("responses", {})

        # Find success response
        for code in ("200", "201", "202", "default"):
            if code in responses:
                resp = responses[code]
                schema = resp.get("schema")
                if schema:
                    data = self.generator.generate(schema)
                    status = int(code) if code.isdigit() else 200
                    return JSONResponse(data, status_code=status)

        return JSONResponse({"success": True})
