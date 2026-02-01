from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.v2.response_builder import SpecResponseBuilder
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
        self.response_builder = SpecResponseBuilder(spec, self.resolver)
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
                if "deviceSettings" in path:
                    return self._get_edge_device_settings(edge, path)
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

    def _parse_time_range(self, request: Request) -> tuple[datetime, datetime, int]:
        """
        Parse start, end time, and interval from query parameters.

        Supports:
        - Unix timestamp in milliseconds (e.g., ?start=1234567890000&end=1234567900000)
        - ISO 8601 format (e.g., ?start=2024-01-30T12:00:00Z&end=2024-01-30T18:00:00Z)
        - interval in minutes (e.g., ?interval=5)

        Defaults to last 1 hour with 5-minute intervals if not provided.
        """
        # Default to last 1 hour
        end = datetime.utcnow()
        start = end - timedelta(hours=1)
        interval_minutes = 5

        # Parse query parameters
        start_param = request.query_params.get("start")
        end_param = request.query_params.get("end")
        interval_param = request.query_params.get("interval")

        try:
            if end_param:
                # Try parsing as Unix timestamp in milliseconds
                if end_param.isdigit():
                    end = datetime.utcfromtimestamp(int(end_param) / 1000.0)
                else:
                    # Try parsing as ISO 8601
                    # Remove 'Z' suffix if present and parse
                    end_param_clean = end_param.rstrip('Z')
                    end = datetime.fromisoformat(end_param_clean)

            if start_param:
                # Try parsing as Unix timestamp in milliseconds
                if start_param.isdigit():
                    start = datetime.utcfromtimestamp(int(start_param) / 1000.0)
                else:
                    # Try parsing as ISO 8601
                    start_param_clean = start_param.rstrip('Z')
                    start = datetime.fromisoformat(start_param_clean)
            elif end_param:
                # If only end is specified, default start to 1 hour before end
                start = end - timedelta(hours=1)

            if interval_param and interval_param.isdigit():
                interval_minutes = int(interval_param)
                # Clamp interval to reasonable values (1-60 minutes)
                interval_minutes = max(1, min(60, interval_minutes))

        except (ValueError, OSError) as e:
            log.warning(f"Failed to parse time parameters: {e}. Using defaults.")
            # Fall back to defaults on error
            end = datetime.utcnow()
            start = end - timedelta(hours=1)
            interval_minutes = 5

        # Validate that start is before end
        if start >= end:
            log.warning(f"Start time {start} is not before end time {end}. Swapping.")
            start, end = end - timedelta(hours=1), start

        return start, end, interval_minutes

    def _get_edge_health_stats(
        self,
        edge,
        path: str,
        request: Request
    ) -> JSONResponse:
        """Get edge health statistics."""
        is_time_series = "timeSeries" in path

        if is_time_series:
            start, end, interval = self._parse_time_range(request)
            series = RealisticGenerator.time_series(
                start, end, interval_minutes=interval, metric_type="health"
            )
            # Build spec-compliant response (EdgeHealthStatsSeriesSchema)
            response = self.response_builder.build_health_stats_series_response(series, path)
            return JSONResponse(response)

        # Aggregate stats - build using response builder for consistency
        edge_state = edge.edge_state
        healthy = (edge_state.value if hasattr(edge_state, 'value') else edge_state) == "CONNECTED"
        health_data = {
            "total": 1,
            "tunnelCount": RealisticGenerator.min_max_avg(
                RealisticGenerator.tunnel_count()
            ),
            "tunnelCountV6": {"min": 0.0, "max": 0.0, "average": 0.0},
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
        }
        response = self.response_builder.build_health_stats_response(health_data, path)
        return JSONResponse(response)

    def _get_edge_link_stats(
        self,
        edge,
        path: str,
        request: Request
    ) -> JSONResponse:
        """Get edge link statistics."""
        is_time_series = "timeSeries" in path
        links = self.store.get_edge_links(edge.logical_id)

        edge_state = edge.edge_state
        healthy = (edge_state.value if hasattr(edge_state, 'value') else edge_state) == "CONNECTED"

        # Build links data for response builder
        links_data = []
        for link in links:
            links_data.append({
                "logicalId": link.logical_id,
                "name": link.name,
                "interface": link.interface,
                "ipAddress": link.ip_address,
                "isp": link.isp,
                "linkState": link.link_state.value if hasattr(link.link_state, 'value') else link.link_state,
                "networkType": link.link_type.value if hasattr(link.link_type, 'value') else "WIRED",
            })

        # Provide default if no links
        if not links_data:
            links_data = [{"logicalId": "default", "name": "link-1", "interface": "GE1"}]

        if is_time_series:
            start, end, interval = self._parse_time_range(request)
            series = RealisticGenerator.time_series(
                start, end, interval_minutes=interval, metric_type="link"
            )
            # Build spec-compliant response (array of LinkStatsSeriesRecord)
            response = self.response_builder.build_link_stats_series_response(series, links_data)
            return JSONResponse(response)

        # Build aggregate stats with traffic data
        for link_data in links_data:
            link_data["txBytes"] = RealisticGenerator.bytes_transferred()
            link_data["rxBytes"] = RealisticGenerator.bytes_transferred()
            link_data["latencyMs"] = RealisticGenerator.latency_ms(healthy)
            link_data["jitterMs"] = RealisticGenerator.jitter_ms(healthy)
            link_data["lossPct"] = RealisticGenerator.loss_pct(healthy)

        # Build spec-compliant response (array directly)
        response = self.response_builder.build_link_stats_response(links_data)
        return JSONResponse(response)

    def _get_edge_flow_stats(
        self,
        edge,
        path: str,
        request: Request
    ) -> JSONResponse:
        """Get edge flow statistics including top talkers.

        Supports query parameters:
        - groupBy: Field to group by (destFQDN, sourceIP, application, etc.)
        - sortBy: Field:direction to sort by (e.g., flowCount:DESC)
        - limit: Number of results to return (default 10)
        - start/end: Time range (currently ignored, returns current snapshot)
        """
        # Parse query parameters
        group_by = request.query_params.get("groupBy", "application")
        sort_by_param = request.query_params.get("sortBy", "flowCount:DESC")
        limit_param = request.query_params.get("limit", "10")

        # Parse sortBy (format: "field:direction" or just "field")
        if ":" in sort_by_param:
            sort_by, sort_order = sort_by_param.split(":", 1)
        else:
            sort_by = sort_by_param
            sort_order = "DESC"

        # Parse limit
        try:
            limit = int(limit_param)
            limit = max(1, min(limit, 100))  # Clamp to reasonable range
        except ValueError:
            limit = 10

        # Generate top talker data
        data = RealisticGenerator.top_talkers(
            group_by=group_by,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Build spec-compliant response (array directly, not wrapped)
        response = self.response_builder.build_flow_stats_response(data)
        return JSONResponse(response)

    def _get_edge_device_settings(
        self,
        edge,
        path: str,
    ) -> JSONResponse:
        """Get edge device settings including WAN link configuration."""
        links = self.store.get_edge_links(edge.logical_id)

        # Convert links to dict format for response builder
        links_data = [
            {
                "logicalId": link.logical_id,
                "name": link.name,
                "interface": link.interface,
                "ipAddress": link.ip_address,
                "isp": link.isp,
                "linkState": link.link_state.value if hasattr(link.link_state, 'value') else link.link_state,
                "upstreamMbps": link.upstream_mbps,
                "downstreamMbps": link.downstream_mbps,
            }
            for link in links
        ]

        edge_data = {
            "logicalId": edge.logical_id,
            "name": edge.name,
            "modelNumber": edge.model_number,
            "softwareVersion": edge.software_version,
        }

        # Build spec-compliant response (BaseDeviceSettings)
        response = self.response_builder.build_device_settings_response(edge_data, links_data, path)
        return JSONResponse(response)

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
