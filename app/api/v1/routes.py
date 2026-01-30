from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .handlers import V1Handler

log = logging.getLogger("vco-sim.v1")


def register_v1_routes(app: FastAPI, spec: Dict[str, Any]) -> int:
    """Register all V1 API routes from spec."""
    handler = V1Handler(spec)
    base_path = spec.get("basePath", "/portal/rest")
    paths = spec.get("paths", {})
    count = 0

    for path, path_item in paths.items():
        full_path = f"{base_path}{path}"

        for method, operation in path_item.items():
            if method == "parameters":
                continue

            # V1 is all POST
            if method.lower() != "post":
                continue

            # Create endpoint closure
            def make_endpoint(p: str, op: Dict[str, Any]):
                async def endpoint(request: Request) -> JSONResponse:
                    return await handler.handle_request(request, p, op)
                endpoint.__name__ = f"v1_{p.replace('/', '_').strip('_')}"
                return endpoint

            endpoint_func = make_endpoint(path, operation)

            app.add_api_route(
                full_path,
                endpoint_func,
                methods=["POST"],
                name=operation.get("operationId", f"v1_{path}"),
                tags=operation.get("tags", ["v1"]),
            )
            count += 1

    log.info("Registered %d V1 routes", count)
    return count
