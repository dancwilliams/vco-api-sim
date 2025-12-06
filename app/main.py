from __future__ import annotations

import copy
import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from .schema_utils import SchemaResolver, example_from_schema
from .spec_loader import cached_spec
from .store import MemoryStore


log = logging.getLogger("vco-sim")

spec = cached_spec()
info = spec.get("info", {})
app = FastAPI(
    title=info.get("title", "VCO Simulator"),
    version=info.get("version", "0.1.0"),
    description=info.get("description", "Mock implementation of the VCO API."),
)

resolver = SchemaResolver(spec)
store = MemoryStore()


def _choose_response_schema(operation: Dict[str, Any]) -> tuple[Optional[Dict[str, Any]], int]:
    responses = operation.get("responses", {}) or {}
    chosen_code: Optional[str] = None
    for code in ("200", "201", "202", "204", "default"):
        if code in responses:
            chosen_code = code
            break
    if chosen_code is None and responses:
        chosen_code = next(iter(responses.keys()))
    if chosen_code is None:
        return None, 200

    status_code = int(chosen_code) if chosen_code.isdigit() else 200
    response_obj = responses.get(chosen_code, {})
    content = (response_obj or {}).get("content", {})
    media = content.get("application/json")
    if not media:
        for media_type, media_schema in content.items():
            if media_type.endswith("+json"):
                media = media_schema
                break
    schema = None
    if media:
        schema = media.get("schema")
    return schema, status_code


def _build_endpoint(
    path: str,
    method: str,
    operation: Dict[str, Any],
    path_params: List[Dict[str, Any]],
    query_params: List[Dict[str, Any]],
    response_schema: Optional[Dict[str, Any]],
    default_status: int,
) -> Any:
    method_lower = method.lower()

    async def endpoint(request: Request) -> Response:
        captured_path_params = dict(request.path_params)
        captured_query_params = dict(request.query_params.multi_items())

        body: Any = None
        if method_lower in {"post", "put", "patch"}:
            try:
                body = await request.json()
            except Exception:
                body = None

        log.debug(
            "Handling %s %s path_params=%s query=%s",
            method_upper,
            path,
            captured_path_params,
            captured_query_params,
        )

        if method_lower in {"post", "put", "patch"}:
            store.set(path, "resource", captured_path_params, body)

        if method_lower == "delete":
            store.delete(path, "resource", captured_path_params)

        payload: Any = None
        if method_lower == "get":
            payload = store.get(path, "resource", captured_path_params)

        if payload is None and response_schema is not None and default_status != 204:
            payload = example_from_schema(response_schema, resolver)
            payload = _inject_known_ids(payload, captured_path_params)

        if payload is None and "/edges/" in path:
            payload = _edge_default_payload(path, captured_path_params)

        if payload is None and default_status != 204:
            payload = {"message": f"Mock response for {method_upper} {path}"}

        if method_lower == "delete" or default_status == 204:
            return Response(status_code=default_status)

        return JSONResponse(payload, status_code=default_status)

    method_upper = method.upper()
    endpoint.__name__ = f"{method_lower}_{path.replace('/', '_').strip('_') or 'root'}"
    return endpoint


def _extract_path_params(path: str) -> List[str]:
    return re.findall(r"{([^}/]+)}", path)


SAMPLE_IDS: Dict[str, str] = {
    "enterpriseLogicalId": "ent-1",
    "enterpriseId": "ent-1",
    "logicalId": "ent-1",
    "edgeLogicalId": "edge-1",
    "edgeId": "edge-1",
    "profileLogicalId": "prof-1",
    "gatewayId": "gw-1",
    "appId": "app-1",
}

CUSTOM_SEEDS: Dict[str, Any] = {
    "/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/healthStats": {
        "_href": "/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/healthStats",
        "total": 1,
        "tunnelCount": {"min": 2, "max": 4, "average": 3},
        "tunnelCountV6": {"min": 0, "max": 0, "average": 0},
        "memoryPct": {"min": 42.1, "max": 65.5, "average": 54.3},
        "flowCount": {"min": 120, "max": 240, "average": 180},
        "cpuPct": {"min": 12.5, "max": 48.3, "average": 28.9},
        "cpuCoreTemp": {"min": 55.0, "max": 73.2, "average": 64.8},
        "handoffQueueDrops": {"min": 0, "max": 2, "average": 0.1},
    },
}


def _inject_known_ids(payload: Any, path_params: Dict[str, Any]) -> Any:
    if isinstance(payload, dict):
        for key, value in path_params.items():
            if key in payload and payload[key] in {None, "", "string"}:
                payload[key] = value
        for key, value in path_params.items():
            if key.endswith("LogicalId") and "logicalId" in payload:
                payload["logicalId"] = value
            if key.endswith("Id") and "id" in payload:
                payload["id"] = value
    if isinstance(payload, list) and payload:
        payload[0] = _inject_known_ids(payload[0], path_params)
    return payload


def _edge_default_payload(path: str, path_params: Dict[str, Any]) -> Any:
    logical_id = path_params.get("edgeLogicalId", "edge-1")
    enterprise_id = path_params.get("enterpriseLogicalId", "ent-1")

    edge_stub = {
        "_href": path.format(**{k: v for k, v in path_params.items()}),
        "enterpriseId": enterprise_id,
        "logicalId": logical_id,
        "name": f"Edge {logical_id}",
        "modelNumber": "VCE-1000",
        "serialNumber": f"VC-{logical_id}",
        "buildNumber": "6.0.0",
        "activationKey": f"ACT-{logical_id}",
        "alertsEnabled": True,
        "site": {"name": "Main Office", "city": "Austin", "country": "US"},
    }

    if path.endswith("/edges/"):
        return {"_href": path, "total": 1, "data": [edge_stub]}

    if path.endswith("/deviceSettings"):
        return {"edge": edge_stub, "deviceSettings": {"lan": [], "wan": []}}

    if path.endswith("/qos"):
        return {"edge": edge_stub, "qos": {"rules": []}}

    if path.endswith("/applications") or "/applications/" in path:
        return {"_href": path, "total": 1, "data": [{"id": "app-1", "name": "Default App"}]}

    if "healthStats/timeSeries" in path:
        return {
            "_href": path,
            "total": 1,
            "series": [
                {"time": 0, "cpuPct": 20, "memoryPct": 50, "tunnelCount": 3, "flowCount": 150}
            ],
        }

    if "healthStats" in path:
        return {
            "_href": path,
            "total": 1,
            "tunnelCount": {"min": 2, "max": 4, "average": 3},
            "tunnelCountV6": {"min": 0, "max": 0, "average": 0},
            "memoryPct": {"min": 42.1, "max": 65.5, "average": 54.3},
            "flowCount": {"min": 120, "max": 240, "average": 180},
            "cpuPct": {"min": 12.5, "max": 48.3, "average": 28.9},
            "cpuCoreTemp": {"min": 55.0, "max": 73.2, "average": 64.8},
            "handoffQueueDrops": {"min": 0, "max": 2, "average": 0.1},
        }

    if "linkStats/timeSeries" in path or "flowStats/timeSeries" in path or "pathStats/timeSeries" in path:
        return {
            "_href": path,
            "total": 1,
            "series": [
                {"time": 0, "txBytes": 1024, "rxBytes": 2048, "latencyMs": 15, "lossPct": 0.1, "jitterMs": 1.2}
            ],
        }

    if "linkStats" in path or "flowStats" in path or "pathStats" in path:
        return {
            "_href": path,
            "total": 1,
            "stats": [
                {"link": "link-1", "txBytes": 1024, "rxBytes": 2048, "latencyMs": 15, "lossPct": 0.1, "jitterMs": 1.2}
            ],
        }

    if "nonSdWanTunnelStatus" in path:
        return {
            "_href": path,
            "total": 1,
            "data": [
                {"name": "vpn-1", "status": "UP", "peer": "198.51.100.1", "uptimeSec": 3600}
            ],
        }

    # Default detail payload
    return edge_stub


def _render_custom_seed(template: Any, path_params: Dict[str, Any]) -> Any:
    """Deep-copy and fill a template payload with path param values."""
    data = copy.deepcopy(template)

    def _fill(value: Any) -> Any:
        if isinstance(value, str):
            return value.format(**path_params)
        if isinstance(value, list):
            return [_fill(v) for v in value]
        if isinstance(value, dict):
            return {k: _fill(v) for k, v in value.items()}
        return value

    return _fill(data)


def seed_store() -> None:
    """Seed the in-memory store with deterministic dummy data for GETs."""
    for path, path_item in spec.get("paths", {}).items():
        path_params_names = _extract_path_params(path)
        path_params = {name: SAMPLE_IDS.get(name, "sample-value") for name in path_params_names}
        for method, operation in path_item.items():
            if method in {"parameters"}:
                continue
            if method.lower() != "get":
                continue
            if path in CUSTOM_SEEDS:
                payload = _render_custom_seed(CUSTOM_SEEDS[path], path_params)
                store.set(path, "resource", path_params, payload)
                continue
            if "/edges/" in path:
                payload = _edge_default_payload(path, path_params)
                store.set(path, "resource", path_params, payload)
                continue

            response_schema, status_code = _choose_response_schema(operation)
            if not response_schema or status_code == 204:
                continue
            payload = example_from_schema(response_schema, resolver)
            if payload is None:
                continue
            payload = _inject_known_ids(payload, path_params)
            store.set(path, "resource", path_params, payload)


def register_routes() -> None:
    for path, path_item in spec.get("paths", {}).items():
        path_level_params = path_item.get("parameters", [])
        for method, operation in path_item.items():
            if method == "parameters":
                continue

            all_params = path_level_params + operation.get("parameters", [])
            path_params = [p for p in all_params if p.get("in") == "path"]
            query_params = [p for p in all_params if p.get("in") == "query"]

            response_schema, status_code = _choose_response_schema(operation)
            endpoint = _build_endpoint(
                path,
                method,
                operation,
                path_params,
                query_params,
                response_schema,
                status_code,
            )
            app.add_api_route(
                path,
                endpoint,
                methods=[method.upper()],
                status_code=status_code,
                name=operation.get("operationId") or f"{method}_{path}",
                tags=operation.get("tags") or [],
            )


@app.on_event("startup")
async def _bootstrap() -> None:
    app.openapi_schema = spec
    app.openapi = lambda: spec
    register_routes()
    seed_store()
    log.info("VCO simulator ready with %s paths", len(spec.get("paths", {})))


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}
