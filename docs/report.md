# CampusRoute AI — Project Report Outline

## Problem and users

Campus security staff, students and faculty often coordinate medicine, books or
documents through calls and messaging. They need a simple pickup/destination
flow, while an agent handles weighted roads, accessibility, battery and route
changes. The project intentionally separates a friendly UI from the technical
search layer.

## Agent formulation

The percepts are current location, nearby roads, blockage state, terrain,
battery, traffic, weather and priority. Actions are choose route, move to the
next node, deliver, mark a road blocked and re-plan. Goals are deliver the item,
avoid blocked roads, preserve battery and reduce time/cost. The environment is
partially observable, single-agent, sequential, weighted, dynamic and mostly
deterministic.

## Search complexity

| Algorithm | Complete | Optimality | Time | Space | Use in this project |
|---|---|---|---|---|---|
| BFS | Yes on finite graphs | Fewest edges | O(V+E) | O(V) | Uniform-cost teaching comparison |
| DFS | No in general | No | O(V+E) | O(V) | Exploration comparison |
| Dijkstra | Yes | Least weighted cost | O((V+E) log V) | O(V) | Low-battery weighted fallback |
| A* | Yes with valid conditions | Least cost | O(E) best-case, exponential worst-case | O(V) | Goal-directed production route |

## Heuristic admissibility sketch

For every road, the stored distance is at least the haversine straight-line
distance between its endpoints. The routing heuristic multiplies the remaining
straight-line distance by the minimum observed generalized cost per kilometre.
Therefore the heuristic cannot exceed the cost of any real road path under the
same conditions: it is a lower bound. With non-negative road costs, A* remains
admissible; with consistent edge costs, its usual graph-search optimality also
holds.

## Safety and resilience

Campus IDs are allow-listed by format and resolved paths are confined to the
maps directory. Map loading rejects impossible road distances and elevation
mismatches. Delivery status changes follow a forward state machine. Storage
writes use a temporary file and `os.replace`; a lock protects concurrent
threads. Live location requires a delivery ID and expires from a bounded cache.

## Limitations and future work

The demo maps are synthetic and must be replaced by a verified OSM/GIS extract.
GPS is nearest-node matching rather than turn-by-turn navigation. JSON storage
is suitable for a demonstration, not a production multi-user deployment.
Next steps are PostgreSQL/PostGIS, authentication, WebSocket tracking, real
traffic/weather providers, map editing approval and load testing.
