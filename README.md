# CampusRoute AI

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![License](https://img.shields.io/badge/license-MIT-green)

CampusRoute AI is an open-source campus logistics and navigation platform for
planning, explaining and simulating deliveries across complex university
environments.

It models a campus as a weighted graph, compares search strategies, selects a
feasible route automatically, accounts for terrain, traffic, weather,
elevation, delivery priority and battery constraints, and supports blocked-road
replanning and multiple deliveries.

The routing engine is independent of any particular university, map provider or
academic assignment. A campus can use its own map data without changing the
core algorithms.

## Why this project exists

Campus delivery systems often depend on static instructions, manual
coordination or disconnected map data. This makes it difficult to handle
blocked roads, accessibility, battery limits, urgent deliveries and multiple
stops. CampusRoute AI makes those decisions visible and explainable.

## Core capabilities

| Capability | Implementation |
|---|---|
| Campus modelling | Locations, weighted roads, boundaries, terrain and elevation |
| Route planning | BFS, DFS, Dijkstra and A* comparison |
| Automatic selection | Feasible strategy selected from route cost and constraints |
| Delivery planning | Books, medicines, documents, food and other small items |
| Priority handling | Normal, high and emergency priorities |
| Battery awareness | Consumption estimate and healthy/low/critical states |
| Dynamic replanning | Recalculation after blocked roads or changed conditions |
| Multiple deliveries | Precedence-aware ordering and combined routes |
| Live tracking | Browser GPS approximation and simulated movement |
| Explainability | Algorithm comparison, cost breakdown and route reason |
| Accessibility | Optional filtering of non-accessible roads |

## Product flow

1. Load a campus map.
2. Select pickup and destination points.
3. Enter item, urgency, battery and optional constraints.
4. Compare feasible routes and select one automatically.
5. Display route, ETA estimate, battery impact and reasoning.
6. Re-plan when an incident blocks a road.
7. Optimise multiple deliveries as one plan.

The user does not need to understand the algorithms. They remain visible for
learning, evaluation and explainability.

## Architecture

```text
Browser UI (vanilla JS + Leaflet)
        │ HTTP/JSON
        ▼
FastAPI API
  ├── map and campus services
  ├── delivery and tracking services
  ├── routing and cost evaluation
  └── multiple-delivery optimisation
        │
        ▼
Graph and data layer
  ├── campus JSON maps
  ├── weighted graph representation
  ├── search algorithms
  └── local JSON persistence
```

## Quick start

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn backend.app.api:app --reload
```

Open a second terminal in the project root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500`. API documentation is available at
`http://127.0.0.1:8000/docs`.

## Project layout

```text
backend/app/
  api.py                    FastAPI application entry point
  graph.py                  Weighted campus graph
  algorithms.py             BFS, DFS, Dijkstra and A*
  costs.py                  Shared route-cost model
  routing.py                Route comparison and selection
  optimization.py           Multiple-delivery planning
  delivery_service.py       Delivery lifecycle and replanning
  maps/*.json               Configurable campus map data
  routes/                   API routers
  validate_map.py           Map validation command
frontend/                   Vanilla JS, CSS and Leaflet UI
tests/                      Unit, API and map-validation tests
docs/                       Architecture, research and readiness notes
```

## Adding a campus

Copy an existing file in `backend/app/maps/`, give every location a stable ID,
add realistic roads and metadata, include a boundary polygon, and validate it:

```powershell
python -m backend.app.validate_map backend/app/maps/your_campus.json
```

Demo maps are synthetic. Replace them with verified GIS, survey or
OpenStreetMap-derived data before operational use.

## Testing and quality

```powershell
python -m pytest -q
python -m ruff check .
```

Tests cover graph validity, search behaviour, route cost, battery rejection,
priority effects, road blocking, replanning, map loading, delivery lifecycle
and API validation.

## Roadmap

- [x] Configurable campus maps
- [x] Weighted graph routing
- [x] BFS, DFS, Dijkstra and A*
- [x] Automatic route comparison and explanation
- [x] Battery, priority, terrain and weather factors
- [x] Blocked-road replanning
- [x] Multiple-delivery optimisation
- [x] Browser map and live-location approximation
- [ ] PostGIS-backed map storage
- [ ] Surveyed indoor and multi-floor maps
- [ ] Production authentication and role management
- [ ] Approved traffic and weather provider integration
- [ ] Robot telemetry and ROS2 integration
- [ ] Fleet assignment and collision-aware planning

## Important limitations

This is a reproducible routing and logistics prototype, not a certified
autonomous-robot controller or safety-critical navigation system. ETA is an
explainable estimate, browser GPS is not reliable for room-level positioning,
local JSON storage is single-instance, and synthetic maps must be replaced with
verified campus data for deployment.

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md), check
existing issues, and add tests whenever behaviour changes.

## Research and references

See [docs/research.md](docs/research.md),
[docs/architecture.md](docs/architecture.md), and
[docs/real-world-readiness.md](docs/real-world-readiness.md).

## License

MIT. See [LICENSE](LICENSE).
