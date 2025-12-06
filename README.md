# VCO API Simulator

A lightweight FastAPI + Pydantic simulator that serves the VMware VeloCloud Orchestrator (VCO) API using the provided OpenAPI document in `vco-api-json/vco_api`.

## Quick start

```bash
# provide your own VCO OpenAPI JSON (set VCO_SPEC_PATH to that file)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set VCO_SPEC_PATH=C:\path\to\vco_api.json
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs` (Swagger) or `http://127.0.0.1:8000/redoc`. The OpenAPI served is exactly the VCO spec you supplied. The repository intentionally does not ship the VCO spec—bring your own to avoid redistribution concerns.

### Using uv (optional)

If you prefer the `uv` workflow:

```bash
uv venv
./.venv/Scripts/activate
uv sync  # uses pyproject.toml / uv.lock if present
set VCO_SPEC_PATH=C:\path\to\vco_api.json
uv run uvicorn app.main:app --reload
```

## Simulator behavior

- Routes are generated dynamically from the OpenAPI file (55 paths, 314 schemas in your spec).
- Path/query parameters are typed based on the schema and parsed by FastAPI/Pydantic.
- Request bodies are accepted as JSON. Basic validation is driven by typing; structure is not enforced beyond that.
- Responses are built from schema/examples/defaults in the spec; otherwise placeholder data is returned. GET routes are pre-seeded with dummy data keyed to sample IDs (`enterpriseLogicalId=ent-1`, `edgeLogicalId=edge-1`, `profileLogicalId=prof-1`, `appId=app-1`). All `/edges/` GET endpoints have basic stub payloads (list/detail plus health/link/flow/path stats).
- A simple in-memory store keeps the last payload sent to `POST`/`PUT`/`PATCH` and returns it on subsequent `GET` for the same resource. `DELETE` clears it. If you request with other IDs, you'll see example-based responses populated with your path params.
- Health check at `/health` returns `{"status": "ok"}`.

## Customizing

- Point `VCO_SPEC_PATH` at a modified spec to change routes without code changes.
- Extend `app/schema_utils.py` if you want richer sample generation.
- Swap `MemoryStore` in `app/store.py` for a persistent backend if you need state across runs.
