from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from app.generators.factory import RealisticGenerator
from app.generators.schema_generator import SchemaGenerator
from app.specs.resolver import SchemaResolver
from app.store.relationships import get_store

log = logging.getLogger("vco-sim.v2")


class V2Handler:
    """Handler for V2 REST endpoints."""

    def __init__(self, spec: Dict[str, Any]) -> None:
        self.spec = spec
        self.resolver = SchemaResolver(spec)
        self.generator = SchemaGenerator(spec)
        self.store = get_store()

    async def handle_get(
        self,
        request: Request,
        path: str,
        operation: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> JSONResponse:
        """Handle GET requests."""
        enterprise_id = path_params.get("enterpriseLogicalId")
        edge_id = path_params.get("edgeLogicalId")

        # Enterprise endpoints
        if "/enterprises/" in path and enterprise_id:
            return self._handle_enterprise_get(path, enterprise_id, edge_id, request)

        # List enterprises
        if path.endswith("/enterprises/"):
            return self._list_enterprises()

        # Fall back to schema-generated response
        return self._generate_response(operation, path_params)

    async def handle_post(
        self,
        request: Request,
        path: str,
        operation: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> JSONResponse:
        """Handle POST requests."""
        body: Dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            pass

        # Generate created resource
        response = self._generate_response(operation, path_params)
        return JSONResponse(response.body, status_code=201)

    async def handle_put(
        self,
        request: Request,
        path: str,
        operation: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> JSONResponse:
        """Handle PUT requests."""
        body: Dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            pass

        return self._generate_response(operation, path_params)

    async def handle_patch(
        self,
        request: Request,
        path: str,
        operation: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> JSONResponse:
        """Handle PATCH requests."""
        body: Dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            pass

        return self._generate_response(operation, path_params)

    async def handle_delete(
        self,
        request: Request,
        path: str,
        operation: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> JSONResponse:
        """Handle DELETE requests."""
        return JSONResponse(None, status_code=204)

    def _handle_enterprise_get(
        self,
        path: str,
        enterprise_id: str,
        edge_id: Optional[str],
        request: Request,
    ) -> JSONResponse:
        """Handle enterprise-scoped GET requests."""
        enterprise = self.store.enterprises.get(enterprise_id)

        # Edge-specific endpoints
        if edge_id:
            edge = self.store.edges.get(edge_id)
            if edge:
                if "healthStats" in path:
                    return self._get_edge_health_stats(edge, path, request)
                if "linkStats" in path:
                    return self._get_edge_link_stats(edge, path, request)
                if "flowStats" in path:
                    return self._get_edge_flow_stats(edge, path, request)
                # Return edge details
                return JSONResponse(edge.to_v2_dict())

        # Enterprise-level endpoints
        if path.endswith("/edges/"):
            edges = self.store.get_enterprise_edges(enterprise_id)
            return JSONResponse({
                "data": [e.to_v2_dict() for e in edges],
                "metaData": {"more": False}
            })

        if path.endswith("/events"):
            return self._get_enterprise_events(enterprise_id)

        if path.endswith("/alerts"):
            return self._get_enterprise_alerts(enterprise_id)

        # Return enterprise details
        if enterprise:
            return JSONResponse(enterprise.to_v2_dict())

        return JSONResponse({"error": "Not found"}, status_code=404)

    def _list_enterprises(self) -> JSONResponse:
        """List all enterprises."""
        enterprises = self.store.enterprises.list()
        return JSONResponse({
            "data": [e.to_v2_dict() for e in enterprises],
            "metaData": {"more": False}
        })

    def _get_edge_health_stats(
        self,
        edge,
        path: str,
        request: Request
    ) -> JSONResponse:
        """Get edge health statistics."""
        is_time_series = "timeSeries" in path

        if is_time_series:
            end = datetime.utcnow()
            start = end - timedelta(hours=1)
            series = RealisticGenerator.time_series(start, end, metric_type="health")
            return JSONResponse({
                "_href": path,
                "total": len(series),
                "series": series,
            })

        # Aggregate stats
        edge_state = edge.edge_state
        healthy = (edge_state.value if hasattr(edge_state, 'value') else edge_state) == "CONNECTED"
        return JSONResponse({
            "_href": path,
            "total": 1,
            "tunnelCount": RealisticGenerator.min_max_avg(
                RealisticGenerator.tunnel_count()
            ),
            "tunnelCountV6": {"min": 0, "max": 0, "average": 0},
            "memoryPct": RealisticGenerator.min_max_avg(
                RealisticGenerator.memory_pct(healthy)
            ),
            "flowCount": RealisticGenerator.min_max_avg(
                RealisticGenerator.flow_count()
            ),
            "cpuPct": RealisticGenerator.min_max_avg(
                RealisticGenerator.cpu_pct(healthy)
            ),
            "cpuCoreTemp": RealisticGenerator.min_max_avg(65.0),
            "handoffQueueDrops": RealisticGenerator.min_max_avg(0.1),
        })

    def _get_edge_link_stats(
        self,
        edge,
        path: str,
        request: Request
    ) -> JSONResponse:
        """Get edge link statistics."""
        is_time_series = "timeSeries" in path
        links = self.store.get_edge_links(edge.logical_id)

        if is_time_series:
            end = datetime.utcnow()
            start = end - timedelta(hours=1)
            series = RealisticGenerator.time_series(start, end, metric_type="link")
            return JSONResponse({
                "_href": path,
                "total": len(series),
                "series": series,
            })

        edge_state = edge.edge_state
        healthy = (edge_state.value if hasattr(edge_state, 'value') else edge_state) == "CONNECTED"
        return JSONResponse({
            "_href": path,
            "total": len(links) or 1,
            "stats": [
                {
                    "link": link.name if links else "link-1",
                    "txBytes": RealisticGenerator.bytes_transferred(),
                    "rxBytes": RealisticGenerator.bytes_transferred(),
                    "latencyMs": RealisticGenerator.latency_ms(healthy),
                    "jitterMs": RealisticGenerator.jitter_ms(healthy),
                    "lossPct": RealisticGenerator.loss_pct(healthy),
                }
                for link in (links or [type("Link", (), {"name": "link-1"})()])
            ],
        })

    def _get_edge_flow_stats(
        self,
        edge,
        path: str,
        request: Request
    ) -> JSONResponse:
        """Get edge flow statistics."""
        return JSONResponse({
            "_href": path,
            "total": 1,
            "data": [
                {
                    "application": "Web",
                    "bytesTx": RealisticGenerator.bytes_transferred(),
                    "bytesRx": RealisticGenerator.bytes_transferred(),
                    "packetsTx": 10000,
                    "packetsRx": 15000,
                }
            ],
        })

    def _get_enterprise_events(self, enterprise_id: str) -> JSONResponse:
        """Get enterprise events."""
        return JSONResponse({
            "data": [
                {
                    "id": 1,
                    "eventTime": datetime.utcnow().isoformat(),
                    "event": "EDGE_UP",
                    "category": "SYSTEM",
                    "severity": "INFO",
                    "message": "Edge came online",
                }
            ],
            "metaData": {"more": False}
        })

    def _get_enterprise_alerts(self, enterprise_id: str) -> JSONResponse:
        """Get enterprise alerts."""
        return JSONResponse({
            "data": [],
            "metaData": {"more": False}
        })

    def _generate_response(
        self,
        operation: Dict[str, Any],
        path_params: Dict[str, str]
    ) -> JSONResponse:
        """Generate response from operation schema."""
        responses = operation.get("responses", {})

        for code in ("200", "201", "202", "default"):
            if code in responses:
                resp = responses[code]
                content = resp.get("content", {})
                json_content = content.get("application/json", {})
                schema = json_content.get("schema")

                if schema:
                    data = self.generator.generate(schema)
                    # Inject path params
                    if isinstance(data, dict):
                        for key, value in path_params.items():
                            if key in data:
                                data[key] = value
                    status = int(code) if code.isdigit() else 200
                    return JSONResponse(data, status_code=status)

        return JSONResponse({})
