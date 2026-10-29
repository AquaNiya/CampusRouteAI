import json
import re
from pathlib import Path

from .graph import CampusGraph, Location

APP_DIRECTORY = Path(__file__).parent
LEGACY_CAMPUS_FILE = APP_DIRECTORY / "campus.json"
MAPS_DIRECTORY = APP_DIRECTORY / "maps"
DEFAULT_CAMPUS_ID = "demo"
DEFAULT_MAX_GPS_DISTANCE_KM = 1.0


def _normalise_campus_id(campus_id: str) -> str:
    value = campus_id.strip().lower()
    return value or DEFAULT_CAMPUS_ID


def _campus_file(campus_id: str) -> Path:
    raw_campus_id = campus_id
    campus_id = _normalise_campus_id(campus_id)

    if not re.fullmatch(r"[a-z0-9_]{1,40}", campus_id):
        raise ValueError(
            f"Invalid campus_id '{raw_campus_id}'. Use 1-40 lowercase letters, "
            "digits or underscores."
        )

    if campus_id == DEFAULT_CAMPUS_ID:
        return LEGACY_CAMPUS_FILE

    maps_root = MAPS_DIRECTORY.resolve()
    candidate = (MAPS_DIRECTORY / f"{campus_id}.json").resolve()

    try:
        candidate.relative_to(maps_root)
    except ValueError as error:
        raise ValueError("Resolved campus map path is outside MAPS_DIRECTORY.") from error

    if not candidate.exists():
        raise FileNotFoundError(
            f"Campus map not found for campus_id='{campus_id}'."
        )

    return candidate


def _read_map_metadata(file_path: Path, campus_id: str) -> dict:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    campus = data.get("campus", {})
    settings = data.get("settings", {})

    return {
        "id": campus_id,
        "name": campus.get("name", campus_id.replace("_", " ").title()),
        "institution": campus.get("institution", "Configurable university campus"),
        "map_version": campus.get("map_version", "1.0"),
        "map_status": campus.get("map_status", "CONFIGURED"),
        "area_acres": campus.get("area_acres"),
        "description": campus.get(
            "description",
            "A campus-specific structural map with walkable locations and roads."
        ),
        "source_url": campus.get("source_url", ""),
        "source_note": campus.get("source_note", ""),
        "max_gps_distance_km": settings.get(
            "max_gps_distance_km",
            DEFAULT_MAX_GPS_DISTANCE_KM
        )
    }


def get_available_campuses() -> list[dict]:
    campuses = [
        _read_map_metadata(LEGACY_CAMPUS_FILE, DEFAULT_CAMPUS_ID)
    ]

    if MAPS_DIRECTORY.exists():
        for file_path in sorted(MAPS_DIRECTORY.glob("*.json")):
            campus_id = file_path.stem.lower()

            if campus_id == DEFAULT_CAMPUS_ID:
                continue

            campuses.append(
                _read_map_metadata(file_path, campus_id)
            )

    return campuses


def load_campus_graph(
    campus_id: str = DEFAULT_CAMPUS_ID
) -> CampusGraph:
    return CampusGraph.from_json(
        _campus_file(campus_id)
    )


def get_campus_max_gps_distance(
    campus_id: str = DEFAULT_CAMPUS_ID
) -> float:
    metadata = _read_map_metadata(
        _campus_file(campus_id),
        _normalise_campus_id(campus_id)
    )
    return float(metadata["max_gps_distance_km"])


def get_campus_boundary(
    campus_id: str = DEFAULT_CAMPUS_ID
) -> list[list[float]]:
    data = json.loads(
        _campus_file(campus_id).read_text(encoding="utf-8")
    )
    return data.get("boundary", [])


def point_inside_boundary(
    latitude: float,
    longitude: float,
    boundary: list[list[float]]
) -> bool:
    if len(boundary) < 3:
        return False

    inside = False
    previous_latitude, previous_longitude = boundary[-1]

    for current_latitude, current_longitude in boundary:
        crosses_latitude = (
            (current_latitude > latitude)
            != (previous_latitude > latitude)
        )

        if crosses_latitude:
            intersection_longitude = (
                (previous_longitude - current_longitude)
                * (latitude - current_latitude)
                / (previous_latitude - current_latitude)
                + current_longitude
            )
            if longitude < intersection_longitude:
                inside = not inside

        previous_latitude = current_latitude
        previous_longitude = current_longitude

    return inside


def get_all_locations(
    graph: CampusGraph
) -> list[dict]:
    return [
        location_to_dict(location)
        for location in graph.locations.values()
    ]


def location_to_dict(
    location: Location
) -> dict:
    return {
        "id": location.id,
        "name": location.name,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "type": location.location_type,
        "elevation": location.elevation
    }


def resolve_location(
    graph: CampusGraph,
    value: str
) -> Location | None:
    normalised_value = value.strip().lower()

    if normalised_value in graph.locations:
        return graph.locations[normalised_value]

    return graph.find_location_by_name(value)


def find_nearest_location(
    graph: CampusGraph,
    latitude: float,
    longitude: float,
    max_distance_km: float = DEFAULT_MAX_GPS_DISTANCE_KM
) -> dict:
    nearest = graph.nearest_location(
        latitude,
        longitude
    )

    distance = graph.distance_between_points(
        latitude,
        longitude,
        nearest.latitude,
        nearest.longitude
    )
    distance_from_user = round(distance, 4)

    result = location_to_dict(nearest)
    result["distance_from_user_km"] = distance_from_user
    result["within_campus"] = (
        distance_from_user <= max_distance_km
    )
    result["max_allowed_distance_km"] = max_distance_km

    if result["within_campus"]:
        result["message"] = (
            "Your location was matched to the nearest campus point."
        )
    else:
        result["message"] = (
            "You appear to be outside the configured campus boundary."
        )

    return result
