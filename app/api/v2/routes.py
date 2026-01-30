from __future__ import annotations

import logging
import re
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .handlers import V2Handler

log = logging.getLogger("vco-sim.v2")


def register_v2_routes(app: FastAPI, spec: Dict[str, Any]) -> int:
    """Register all V2 API routes from spec."""
    handler = V2Handler(spec)
    paths = spec.get("paths", {})
    count = 0

    for path, path_item in paths.items():
        # Extract path parameters
        param_names = re.findall(r"\{([^}]+)\}", path)

        for method, operation in path_item.items():
            if method in ("parameters", "servers"):
                continue

            method_lower = method.lower()

            # Create endpoint closure
            def make_endpoint(p: str, m: str, op: Dict[str, Any], params: list):
                async def endpoint(request: Request) -> JSONResponse:
                    path_params = dict(request.path_params)

                    if m == "get":
                        return await handler.handle_get(request, p, op, path_params)
                    elif m == "post":
                        return await handler.handle_post(request, p, op, path_params)
                    elif m == "put":
                        return await handler.handle_put(request, p, op, path_params)
                    elif m == "patch":
                        return await handler.handle_patch(request, p, op, path_params)
                    elif m == "delete":
                        return await handler.handle_delete(request, p, op, path_params)

                    return JSONResponse({"error": "Method not allowed"}, status_code=405)

                endpoint.__name__ = f"v2_{m}_{p.replace('/', '_').strip('_')}"
                return endpoint

            endpoint_func = make_endpoint(path, method_lower, operation, param_names)

            # Determine status code
            status_code = 200
            if method_lower == "post":
                status_code = 201
            elif method_lower == "delete":
                status_code = 204

            app.add_api_route(
                path,
                endpoint_func,
                methods=[method.upper()],
                status_code=status_code,
                name=operation.get("operationId", f"v2_{method}_{path}"),
                tags=operation.get("tags", ["v2"]),
            )
            count += 1

    log.info("Registered %d V2 routes", count)
    return count
