# Adding a college map

Keep the default map in `../campus.json` for the demo. To add another college,
copy the same JSON structure into this folder using a lowercase identifier:

```text
backend/app/maps/dit_university.json
backend/app/maps/graphic_era.json
```

The backend automatically exposes every JSON file here through
`GET /api/campuses`. The frontend then lets the user choose the campus before
loading locations and planning a route.

Each map should contain:

- `campus.name`
- `campus.institution`
- `campus.map_version`
- `campus.map_status` (`VERIFIED` only when the source has been checked; use `DEMO` for illustrative data)
- `campus.area_acres` (optional; never guess this value)
- `campus.description`
- `campus.source_url` and `campus.source_note`
- `settings.max_gps_distance_km`
- `locations` with IDs, names, coordinates and elevation
- `roads` with distance, terrain, accessibility and direction

Validate a map before adding it to a deployment:

```text
python -m backend.app.validate_map backend/app/maps/himalayan_demo.json
```

The loader also rejects roads shorter than their haversine endpoint distance and
rejects elevation-gain values that disagree with the location elevations.

Do not copy a building name from one university into another university's map.
The map is campus-specific. For a new university, use an official campus map,
surveyed GPS points, or a verified OpenStreetMap extract and then create the
location nodes and walkable road edges from that source.
