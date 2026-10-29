# P-17 Requirement and Evidence Matrix

| Faculty task | Implementation | How to demonstrate | Test/evidence |
|---|---|---|---|
| Represent campus locations and roads as a weighted graph | `graph.py`, `campus.json` | Explain nodes, edges, distance, terrain and elevation | `test_graph.py` |
| Define percepts, actions and goals | `agent.py` | Show `AgentPercepts`, `DeliveryAgent` methods and `AgentGoals` | `test_agent.py` |
| Implement BFS | `algorithms.py` | Run route comparison or explain queue traversal | `test_algorithms.py` |
| Implement DFS | `algorithms.py` | Run route comparison or explain stack traversal | `test_algorithms.py` |
| Implement A* | `algorithms.py`, `routing.py` | Explain `f(n)=g(n)+h(n)` and GPS heuristic | `test_algorithms.py` |
| Calculate shortest/least-cost route | `routing.py` | Compare distance and weighted route cost | `test_routing.py` |
| Add battery consumption | `routing.py`, `simulation.py` | Change battery in Operator options or CLI | battery feasibility tests |
| Add delivery priority | `models.py`, `algorithms.py` | Test Normal, High and Emergency deliveries | priority tests |
| Estimate time and explain delays | `routing.py` | Change traffic/weather in Operator options | route condition output |
| Re-plan blocked paths | `simulation.py`, `graph.py` | Block Main Gate → South Parking during simulation | `test_simulation.py` |
| Classify agent environment | `agent.py`, `/api/agent/environment` | Show PEAS/environment classification in viva | `test_agent.py` |
| Display robot state and planned route | `agent.py`, frontend tracking panel | Show current point, route, battery, ETA and status | CLI + browser demo |
| Create Python simulation | `main.py`, `simulation.py` | Run `python -m backend.app.main` | `test_simulation.py` |
| Plan multiple deliveries | `optimization.py`, `optimization_demo.py` | Run the optimizer with two or more tasks | `test_optimization.py` |
| User-facing batch delivery flow | `/api/deliveries/optimize`, frontend batch panel | Add multiple delivery rows and optimise | browser demo |
| Support different universities | `map_service.py`, `maps/` | Add `<campus_id>.json` and select it in UI | campus loader tests |

## Important academic clarification

BFS and DFS are implemented and evaluated, but they are not blindly used for
every real delivery. BFS is optimal only when edge costs are equal. DFS does
not guarantee a shortest or least-cost route. Dijkstra is used for weighted
energy-aware routing when the battery is low, and A* is used when a valid
geographic heuristic is available. This is an intentional AI design decision,
not a missing feature.
