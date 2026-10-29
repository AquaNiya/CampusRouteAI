# Architecture

```mermaid
flowchart TD
    User["User / faculty demo"] --> UI["Vanilla JS + Leaflet UI"]
    UI --> API["FastAPI application"]
    API --> Routers["Campus / routing / delivery / tracking routers"]
    Routers --> Services["Map service + delivery service"]
    Services --> Search["BFS / DFS / Dijkstra / A*"]
    Services --> Optimizer["Precedence-aware delivery optimizer"]
    Search --> Graph["CampusGraph weighted roads"]
    Services --> Store["Atomic JSON storage"]
```

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web UI
    participant R as Route API
    participant G as Campus graph
    participant S as Search layer
    U->>W: Choose campus, pickup and destination
    W->>R: POST /api/deliveries
    R->>G: Load validated nodes and roads
    R->>S: Compare and select feasible search
    S-->>R: Path and cost metrics
    R-->>W: Delivery, ETA, battery and explanation
    W-->>U: Map, marker and progress status
```

The faculty-fixed algorithm and cost files remain isolated. Routers validate
requests, services resolve campus data, and response models keep the public
JSON contract stable. The API cache is process-local; JSON persistence is safe
against partial writes but is not a multi-node database.
