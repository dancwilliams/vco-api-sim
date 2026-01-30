# VCO API Simulator

A comprehensive FastAPI + Pydantic simulator for the Arista VeloCloud Orchestrator (VCO) API. Supports both the V1 JSON-RPC API (340 endpoints) and V2 REST API (72 endpoints) with realistic fake data generation and stateful entity relationships.

## Features

- **Dual API Support**: Serves both V1 (`/portal/rest/*`) and V2 (`/api/sdwan/v2/*`) APIs simultaneously
- **Realistic Data Generation**: Uses Faker to generate realistic company names, IP addresses, locations, and SD-WAN metrics
- **Stateful Relationships**: Maintains proper entity relationships (Enterprise → Edge → Link)
- **Time Series Data**: Generates realistic time series for health stats, link stats, and flow stats
- **Configurable Seeding**: Control the number of enterprises, edges, and links via environment variables
- **Persistent Enterprise IDs**: Enterprise logical IDs are preserved between restarts via a state file
- **Dynamic Route Generation**: Routes are generated from OpenAPI specs at startup

## Quick Start

### Using uv (recommended)

```bash
# Clone the repository
git clone <repo-url>
cd vco-api-sim

# Install dependencies
uv sync

# Start the simulator
uv run uvicorn app.main:app --reload
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .

# Start the simulator
uvicorn app.main:app --reload
```

### Access the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Status**: http://localhost:8000/status

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check - returns `{"status": "ok"}` |
| `/status` | GET | Shows count of seeded entities |
| `/portal/` | POST | Legacy JSON-RPC endpoint |

### V1 API (JSON-RPC Style)

All V1 endpoints use POST method at `/portal/rest/*`. Examples:

```bash
# Login
curl -X POST http://localhost:8000/portal/rest/login/enterpriseLogin \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'

# Get enterprise edges
curl -X POST http://localhost:8000/portal/rest/enterprise/getEnterpriseEdges \
  -H "Content-Type: application/json" \
  -d '{"enterpriseId": 1}'

# Get edge health
curl -X POST http://localhost:8000/portal/rest/metrics/getEdgeStatusMetrics \
  -H "Content-Type: application/json" \
  -d '{"enterpriseId": 1, "edgeId": 1}'
```

### V2 API (REST Style)

V2 endpoints follow REST conventions at `/api/sdwan/v2/*`. Examples:

```bash
# List enterprises
curl http://localhost:8000/api/sdwan/v2/enterprises/

# Get enterprise edges (replace {enterpriseLogicalId} with actual ID from list)
curl http://localhost:8000/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/

# Get edge health stats
curl http://localhost:8000/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/healthStats

# Get edge health stats time series
curl http://localhost:8000/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/healthStats/timeSeries
```

## Configuration

Configure the simulator using environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `VCO_V1_SPEC_PATH` | Auto-detected | Path to V1 OpenAPI spec (Swagger 2.0) |
| `VCO_V2_SPEC_PATH` | Auto-detected | Path to V2 OpenAPI spec (OpenAPI 3.0) |
| `VCO_SEED_ENTERPRISES` | `2` | Number of enterprises to seed |
| `VCO_SEED_EDGES` | `5` | Number of edges per enterprise |
| `VCO_SEED_LINKS` | `2` | Number of WAN links per edge |
| `VCO_STATE_FILE` | `state.json` | Path to state file for persisting enterprise IDs |
| `VCO_HOST` | `0.0.0.0` | Server bind host |
| `VCO_PORT` | `8000` | Server bind port |
| `VCO_DEBUG` | `false` | Enable debug mode |

### Example .env file

```env
VCO_SEED_ENTERPRISES=5
VCO_SEED_EDGES=10
VCO_SEED_LINKS=3
```

## OpenAPI Specs

The simulator automatically detects OpenAPI specs in the repository root:

- `VC-SD-WAN-6.4-v1.json` - V1 API (Swagger 2.0, 340 endpoints)
- `VC-SD-WAN-6.4-v2.json` - V2 API (OpenAPI 3.0, 55 paths → 72 routes)

You can also specify custom paths via environment variables.

## Data Model

The simulator maintains a relational data model:

```
Enterprise (Customer)
├── id, logicalId, name
├── alertsEnabled, networkId
└── edges[]
    └── Edge
        ├── id, logicalId, name
        ├── edgeState (CONNECTED, DEGRADED, OFFLINE)
        ├── modelNumber, softwareVersion, serialNumber
        ├── site (city, state, country, lat, lon)
        └── links[]
            └── Link
                ├── id, logicalId, name
                ├── interface (GE1, GE2, LTE1, etc.)
                ├── linkState (STABLE, STANDBY, DEAD)
                ├── isp, ipAddress
                └── metrics (latency, jitter, loss)
```

### Seeded Data Distribution

- **Edge States**: 70% CONNECTED, 20% DEGRADED, 10% OFFLINE
- **Link States**: Primary link STABLE (if edge healthy), others STANDBY
- **Locations**: Random US cities (Austin, Denver, Seattle, NYC, LA, etc.)
- **ISPs**: AT&T, Verizon, Comcast, Spectrum, CenturyLink, Cox, Frontier

## Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration and environment variables
├── state.py                # State persistence for enterprise IDs
├── models/                 # Pydantic models
│   ├── base.py             # Base models and mixins
│   ├── enterprise.py       # Enterprise/Customer model
│   ├── edge.py             # Edge device model
│   ├── link.py             # WAN link model
│   └── metrics.py          # Health/stats metrics models
├── store/                  # Data storage layer
│   ├── base.py             # Abstract store interface
│   ├── memory.py           # In-memory implementation with indexes
│   └── relationships.py    # Entity relationship manager
├── generators/             # Fake data generation
│   ├── factory.py          # Realistic SD-WAN data generators
│   └── schema_generator.py # OpenAPI schema-based generation
├── api/                    # API route handlers
│   ├── v1/                 # V1 JSON-RPC handlers
│   │   ├── handlers.py     # Request handlers
│   │   └── routes.py       # Route registration
│   └── v2/                 # V2 REST handlers
│       ├── handlers.py     # Request handlers
│       └── routes.py       # Route registration
├── specs/                  # OpenAPI spec handling
│   ├── loader.py           # Multi-spec loader
│   └── resolver.py         # $ref resolution
└── seeding/                # Data seeding
    └── seed_data.py        # Initial data population
```

## Development

### Install dev dependencies

```bash
uv sync --all-extras
```

### Run with auto-reload

```bash
uv run uvicorn app.main:app --reload
```

### Run tests

```bash
uv run pytest
```

### Lint code

```bash
uv run ruff check .
uv run ruff format .
```

## Simulator Behavior

### Authentication

All authentication endpoints accept any credentials and return success. No actual authentication is enforced - all API calls are accepted.

### Data Persistence

Data is stored in-memory and reset on restart, with one exception: **enterprise logical IDs are persisted** to `state.json` (configurable via `VCO_STATE_FILE`). This ensures enterprise IDs remain stable across restarts while edge and link data is regenerated fresh each time.

### Response Generation

1. **Stored Data**: If data exists in the store (from seeding or previous writes), it's returned
2. **Schema Generation**: If no stored data, responses are generated from OpenAPI schemas
3. **Realistic Defaults**: Metrics and time series use realistic SD-WAN values

### Time Series

Time series endpoints (`/healthStats/timeSeries`, `/linkStats/timeSeries`, etc.) generate data points at 5-minute intervals for the past hour with realistic metric values.

## Examples

### Get all seeded enterprises and their edges

```bash
# Get enterprises
ENTERPRISES=$(curl -s http://localhost:8000/api/sdwan/v2/enterprises/)
echo "$ENTERPRISES" | jq '.data[].logicalId'

# Get edges for first enterprise
ENT_ID=$(echo "$ENTERPRISES" | jq -r '.data[0].logicalId')
curl -s "http://localhost:8000/api/sdwan/v2/enterprises/${ENT_ID}/edges/" | jq '.data'
```

### Get edge health metrics

```bash
ENT_ID="<enterprise-logical-id>"
EDGE_ID="<edge-logical-id>"

# Aggregate stats
curl -s "http://localhost:8000/api/sdwan/v2/enterprises/${ENT_ID}/edges/${EDGE_ID}/healthStats" | jq

# Time series
curl -s "http://localhost:8000/api/sdwan/v2/enterprises/${ENT_ID}/edges/${EDGE_ID}/healthStats/timeSeries" | jq '.series[:3]'
```

## License

This project is provided as-is for testing and development purposes.
