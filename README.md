# CampusRoute AI

![CI](https://img.shields.io/github/actions/workflow/status/example/campusroute/ci.yml?label=CI)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

CampusRoute AI is a third-year AI project for P-17: an agent that plans and
simulates books, medicine and document deliveries across a university campus.
It models locations and roads as a weighted graph, implements BFS, DFS,
Dijkstra and A*, accounts for terrain, traffic, weather, elevation, battery and
priority, re-plans blocked routes, and optimises multiple deliveries.

## Quick start

```text
python -m pip install -r requirements-dev.txt
python -m uvicorn backend.app.api:app --reload
python -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500`. API docs: `http://127.0.0.1:8000/docs`.

## Product flow

1. Select a campus map.
2. Select pickup and destination; the user never selects an algorithm.
3. The routing layer compares required searches and chooses a feasible strategy.
4. The result shows route, ETA, cost, battery, delay reasons and algorithm analysis.
5. A blocked road can trigger re-planning; multiple deliveries use precedence-aware optimisation.

## Project layout

```text
backend/app/
  api.py, settings.py, response_models.py, exception_handlers.py
  routes/             # campus, routing, delivery and tracking routers
  algorithms.py       # faculty-fixed BFS, DFS, Dijkstra and A*
  costs.py            # faculty-fixed shared cost model
  routing.py          # faculty-fixed selection and cost logic
  optimization.py     # faculty-fixed objective function
  maps/*.json         # campus-specific demo maps
frontend/             # vanilla JS, Leaflet and OpenStreetMap
tests/                # unit, API and map-validation tests
docs/                 # architecture, report, research and matrix
```

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/campuses` | List campus maps |
| GET | `/api/map?campus_id=demo` | Locations, roads and boundary |
| POST | `/api/route` | Plan one route |
| POST | `/api/route/compare` | Compare all searches |
| POST | `/api/deliveries` | Create and persist a delivery |
| GET | `/api/deliveries?limit=50&offset=0` | Paginated delivery history |
| POST | `/api/deliveries/{id}/replan` | Re-plan a delivery |
| POST | `/api/deliveries/{id}/confirm` | Confirm delivery with demo receiver code |
| POST | `/api/deliveries/optimize` | Optimise multiple deliveries |
| POST | `/api/live-location` | Store a delivery's live GPS point |
| POST | `/api/roads/block` | Admin road-block simulation |

Every error has `{ "error": "...", "detail": ... }`. Set
`CAMPUSROUTE_ADMIN_KEY` to protect road-block operations. Configure
`CAMPUSROUTE_CORS_ORIGINS`, `CAMPUSROUTE_DATA_DIR`, and
`CAMPUSROUTE_LIVE_LOCATION_TTL_SECONDS` through the environment.

## Tests and quality

```text
python -m pytest -q
python -m ruff check .
python -m backend.app.validate_map backend/app/maps/himalayan_demo.json
```

The CI workflow runs Ruff and pytest on Python 3.12 and 3.13. The maps are
synthetic DEMO maps; replace them with a verified campus GIS/OSM extract before
operational use. GPS matching is a nearest-campus-point approximation, not a
turn-by-turn navigation guarantee. JSON storage is local and single-instance.

## Faculty requirement → file → test

| Requirement | Implementation | Verification |
|---|---|---|
| Weighted graph | `graph.py`, `campus.json` | `test_graph.py` |
| BFS, DFS, A* | `algorithms.py` | `test_algorithms.py` |
| Least-cost route | `costs.py`, `routing.py` | `test_costs.py`, `test_routing.py` |
| Battery and priority | `costs.py`, `optimization.py` | `test_costs.py`, `test_optimization.py` |
| Blockage re-planning | `simulation.py`, delivery router | `test_simulation.py` |
| Agent percepts/goals | `agent.py` | `test_agent.py` |
| Multi-delivery search | `optimization.py` | `test_optimization.py` |
| Map safety | `graph.py`, `validate_map.py` | `test_graph.py`, hardening tests |
| User-friendly tracking | `frontend/`, `routes/tracking.py` | API validation tests |

## Screenshots/GIF placeholders

Add a screenshot of the map view, route result and algorithm comparison here
before submission. A short GIF should show a road being blocked and the route
being recalculated.

## License

MIT. See [LICENSE](LICENSE).

Research notes and the full edge-case catalogue are in
`docs/research.md` and `docs/test-catalogue.md`. The honest production boundary
is documented in `docs/real-world-readiness.md`.
