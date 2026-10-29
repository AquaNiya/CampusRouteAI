# Real-world readiness boundary

CampusRoute AI is a reliable academic software prototype, not a certified
robot-control or campus-safety system. The following boundary is intentional.

## Implemented in the current prototype

| Capability | What is implemented | Real-world caveat |
|---|---|---|
| Campus maps | Configurable JSON campus maps, boundaries, roads and metadata | Replace DEMO data with verified GIS/OSM survey data |
| Search and routing | BFS, DFS, Dijkstra and A* comparison with automatic selection | Search is only as correct as the road graph |
| Multiple deliveries | Precedence-aware order, coloured map segments, numbered stops and battery breakdown | Fleet assignment is not implemented |
| Battery awareness | Healthy/low/critical states and per-leg remaining battery | Real motor telemetry is required for deployment |
| Dynamic incidents | Admin-protected road block, severity, reason, open/resolved incident state and re-planning | Incident data is process-local in this prototype |
| Delivery lifecycle | Assigned, in-transit, delivered, failed, cancelled and replanning states | Production requires audited event history |
| Proof of delivery | Demo OTP/confirmation endpoint and receiver metadata | Production code must be delivered privately by SMS/app, not returned in API response |
| GPS | Browser GPS nearest-campus-point matching and live-location cache | Indoor GPS is not reliable enough for room-level navigation |
| Offline shell | Service worker caches the web interface | API, live GPS and OSM tiles still need connectivity |
| Accessibility | Accessible-only edge filtering | Real accessibility requires verified ramps, doors, lifts and time restrictions |

## Not honestly implementable without external systems

1. Physical robot movement, obstacle avoidance, emergency stop and charging
   require AMR hardware, sensors and a robotics stack such as ROS2.
2. Indoor room-level or multi-floor positioning requires surveyed floor plans
   plus Wi-Fi/Bluetooth/UWB/beacon infrastructure; ordinary browser GPS cannot
   guarantee it.
3. Live traffic and weather require an approved provider, API key, rate limits,
   data freshness checks and a fallback policy.
4. Production authentication, role management and privacy compliance require an
   identity provider, HTTPS, audit logs, consent and institutional policy.
5. Multi-user durable storage requires PostgreSQL/PostGIS or an equivalent
   managed database; local JSON is deliberately single-instance.
6. Fleet management requires robot capability matching, task assignment,
   telemetry, collision avoidance and recovery protocols.
7. Guaranteed ETA requires calibrated field measurements and historical data;
   the current ETA is an explainable estimate.

These items are not hidden gaps. They are documented extension boundaries so a
faculty reviewer can distinguish a reproducible AI routing prototype from an
operational safety-critical deployment.
