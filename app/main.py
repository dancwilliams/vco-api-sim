from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.routes import register_v1_routes
from app.api.v2.routes import register_v2_routes
from app.config import get_settings
from app.seeding.seed_data import seed_all
from app.specs.loader import get_v1_spec, get_v2_spec
from app.store.relationships import get_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("vco-sim")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    log.info("Starting VCO API Simulator...")

    v1_spec = get_v1_spec()
    v2_spec = get_v2_spec()

    v1_count = 0
    v2_count = 0

    if v1_spec:
        v1_count = register_v1_routes(app, v1_spec)
        log.info("Loaded V1 spec: %d paths", len(v1_spec.get("paths", {})))
    else:
        log.warning("V1 spec not found")

    if v2_spec:
        v2_count = register_v2_routes(app, v2_spec)
        log.info("Loaded V2 spec: %d paths", len(v2_spec.get("paths", {})))
    else:
        log.warning("V2 spec not found")

    # Seed data
    seed_all()

    store = get_store()
    log.info(
        "VCO Simulator ready: %d V1 routes, %d V2 routes, "
        "%d enterprises, %d edges, %d links",
        v1_count,
        v2_count,
        store.enterprises.count(),
        store.edges.count(),
        store.links.count(),
    )

    yield

    # Shutdown
    log.info("Shutting down VCO API Simulator")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title="VCO API Simulator",
    version="0.2.0",
    description="Mock implementation of the Arista VeloCloud Orchestrator API (V1 + V2)",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/status")
async def status() -> Dict[str, Any]:
    """Status endpoint showing loaded data."""
    store = get_store()
    return {
        "status": "ok",
        "data": {
            "enterprises": store.enterprises.count(),
            "edges": store.edges.count(),
            "links": store.links.count(),
        }
    }


# Support legacy JSON-RPC endpoint at /portal/
@app.post("/portal/")
async def jsonrpc_portal(request: Request) -> JSONResponse:
    """Legacy JSON-RPC endpoint."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    method = body.get("method", "")
    params = body.get("params", {})
    req_id = body.get("id", 1)

    # Return a helpful message pointing to REST endpoints
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {"message": f"Method {method} - use REST endpoints instead"},
    })
