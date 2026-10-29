# Research and design basis

This project is an academic implementation, not a claim of a new routing
algorithm. Its design is grounded in established ideas:

1. Russell and Norvig, *Artificial Intelligence: A Modern Approach*, search,
   agents and environment classification. This motivates the percept/action/
   goal model and the BFS, DFS and A* comparison.
2. Hart, Nilsson and Raphael, “A Formal Basis for the Heuristic Determination
   of Minimum Cost Paths” (1968). This motivates the A* lower-bound heuristic.
3. Dijkstra, “A Note on Two Problems in Connexion with Graphs” (1959). This
   motivates the least-cost baseline for weighted roads.
4. Toth and Vigo, *Vehicle Routing: Problems, Methods, and Applications*.
   This motivates precedence constraints, priority penalties and a practical
   nearest-neighbour plus 2-opt fallback for multiple deliveries.
5. OpenStreetMap contributors. The UI is ready for OSM tiles, but the included
   maps are explicitly synthetic DEMO data and should not be presented as a
   surveyed campus map.

## Direct project references

- [Mappedin: Implementing a successful campus navigation app](https://www.mappedin.com/resources/blog/implementing-a-successful-campus-navigation-app/)
  inspired the searchable campus points, visible map context, accessibility
  thinking, outdoor/indoor extensibility and map-maintenance notes.
- [Ally, Lin and McGreal: An intelligent agent for adapting and delivering
  electronic course materials to mobile learners](https://www.researchgate.net/publication/228623389_An_intelligent_agent_for_adapting_and_delivering_electronic_course_materials_to_mobile_learners)
  inspired the thin-client approach: keep computation and adaptation on the
  server while the client remains simple for heterogeneous devices.
- [ACM reference supplied for the project](https://dl.acm.org/doi/10.1145/3675888.3676146)
  is retained as a related-work pointer. The ACM page may require institutional
  access, so it is not treated as a verified technical claim here.

These sources are references, not copied implementation. CampusRoute AI uses a
small, explainable graph simulation rather than claiming physical AMR control,
indoor positioning accuracy or production fleet autonomy.

## How the two demo campuses differ

`himalayan_demo.json` is a hilly test profile: it contains larger elevation
changes, steep/gravel/mud terrain, inaccessible links and one-way edges. It is
useful for testing battery impact, accessibility filtering, weather sensitivity
and re-planning. `plains_demo.json` is a flatter profile: paved links dominate
and elevation changes are smaller, while a few rough or restricted links keep
the search comparison meaningful. Both are synthetic DEMO maps, not official
maps of named universities.

The project contribution is integration and transparent evaluation: each route
result exposes the selected strategy, competing search outcomes, cost, battery,
ETA and delay reasons so a faculty reviewer can trace the decision.
