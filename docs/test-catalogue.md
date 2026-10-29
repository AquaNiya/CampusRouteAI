# CampusRoute AI: Test Catalogue

This catalogue describes the checks used to verify the P-17 requirements and
the safety boundaries of the demonstration system.

## Functional tests

| Area | Test | Expected result |
|---|---|---|
| Map | Load every demo map | Nodes, roads, boundary and metadata load successfully |
| Map | Validate endpoint coordinates | A road shorter than its straight-line endpoint distance is rejected |
| Map | Validate elevations | Road elevation gain agrees with endpoint elevations within tolerance |
| Search | BFS | Returns a route with the fewest graph edges when one exists |
| Search | DFS | Returns a valid exploratory route, without claiming optimality |
| Search | Dijkstra | Returns the least-cost route for non-negative edge costs |
| Search | A* | Returns the least-cost route when the validated heuristic is admissible |
| Cost | Priority | Emergency and high-priority jobs affect weighted route cost |
| Cost | Weather | Rain/storm conditions increase cost or make unsafe roads unavailable |
| Cost | Traffic | Severe traffic can change route ranking on a competing-route graph |
| Battery | Insufficient battery | A route is rejected or marked `battery_insufficient` with a clear reason |
| Battery | State | The UI reports healthy, low and critical battery states |
| Replanning | Block a road | The route avoids the blocked road and records the re-plan reason |
| Replanning | No alternative | The system reports failure instead of inventing a route |
| Delivery | Status transition | Invalid transitions return a conflict response |
| Delivery | Confirmation | Delivery becomes complete only after receiver confirmation in demo mode |
| Delivery | Cancellation/failure | The status and reason are visible in delivery history |
| Tracking | Missing delivery ID | The live-location request is rejected with validation detail |
| Tracking | Location cache | Entries expire and the cache remains bounded |
| Multi-stop | Interleaving | Pickup/drop-off precedence is preserved while order is optimised |
| Multi-stop | Large stop set | Nearest-neighbour plus 2-opt is used above the brute-force limit |
| UI | Multiple deliveries | Each segment is shown with its own colour, stop number and state |
| UI | Map labels | Building names appear on hover/focus, not as an unexplained list only |
| UI | Accessibility | Controls have labels, keyboard focus and readable status text |

## Manual faculty demonstration

1. Open the demo and select a campus map.
2. Create one normal delivery and show the route, ETA, distance, cost and
   algorithm analysis.
3. Create a high-priority delivery and compare the reason and weighted cost.
4. Change weather to rain or storm and show the updated ETA/cost.
5. Block a road and re-plan. Point out the changed path and reason.
6. Create two or more deliveries. Show the optimised order and all coloured
   route segments on the map.
7. Reduce battery below the required reserve and show the safe rejection.
8. Confirm a delivery and show its status changing to delivered.
9. Open the API documentation at `/docs` and show the route, delivery and
   tracking endpoints.
10. Run the automated suite before submission.

## Real-world boundary

The current maps and weather/traffic inputs are controlled demonstration data.
They are intentionally labelled `DEMO`. A production deployment must replace
them with a verified GIS/OSM or university map, authenticated telemetry from a
robot battery-management system, a weather provider, a campus traffic source,
and measured delivery history. The application must report an estimated ETA
with a confidence range; it must not promise a physically guaranteed arrival
time.

## Final quality commands

```text
python -m pytest -q
python -m ruff check .
node --check frontend/app.js
python -m compileall -q backend
```
