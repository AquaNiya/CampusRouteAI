from fastapi import APIRouter

from ..agent import classify_environment
from ..map_service import (
    find_nearest_location,
    get_all_locations,
    get_available_campuses,
    get_campus_boundary,
    get_campus_max_gps_distance,
    point_inside_boundary,
)
from ..response_models import ApiDict, ApiListItem
from ..runtime import incident_cache, get_graph, graph_cache
from ..settings import settings

router = APIRouter()


@router.get("/", response_model=ApiDict)
def home() -> dict:
    return {"application": "CampusRoute AI", "status": "running"}


@router.get("/api/health", response_model=ApiDict)
def health_check() -> dict:
    return {
        "status": "healthy",
        "campuses": len(get_available_campuses()),
        "loaded_campuses": list(graph_cache),
    }


@router.get("/api/version", response_model=ApiDict)
def version() -> dict:
    return {
        "name": "CampusRoute AI",
        "version": "1.1.0",
        "api_base": settings.api_base,
    }


@router.get("/api/agent/environment", response_model=ApiDict)
def agent_environment() -> dict:
    return classify_environment()


@router.get("/api/campuses", response_model=list[ApiListItem])
def campuses() -> list[dict]:
    return get_available_campuses()


@router.get("/api/locations", response_model=list[ApiListItem])
def locations(campus_id: str = "demo") -> list[dict]:
    return get_all_locations(get_graph(campus_id))


@router.get("/api/map", response_model=ApiDict)
def campus_map(campus_id: str = "demo") -> dict:
    graph = get_graph(campus_id)
    roads = []
    seen: set[tuple[str, str]] = set()
    for neighbours in graph.adjacency.values():
        for road in neighbours:
            key = tuple(sorted((road.source, road.destination)))
            if key in seen:
                continue
            seen.add(key)
            roads.append(
                {
                    "source": road.source,
                    "destination": road.destination,
                    "distance": road.distance,
                    "elevation_gain": road.elevation_gain,
                    "terrain": road.terrain,
                    "accessible": road.accessible,
                    "blocked": road.blocked
                    or (road.source, road.destination) in graph.blocked_roads,
                }
            )
    normalized = campus_id.strip().lower() or "demo"
    metadata = next(
        (campus for campus in get_available_campuses() if campus["id"] == normalized),
        None,
    )
    return {
        "campus": metadata,
        "boundary": get_campus_boundary(campus_id),
        "locations": get_all_locations(graph),
        "roads": roads,
        "incidents": incident_cache.get(normalized, []),
    }


@router.get("/api/nearest", response_model=ApiDict)
def nearest_location(latitude: float, longitude: float, campus_id: str = "demo") -> dict:
    graph = get_graph(campus_id)
    nearest = find_nearest_location(
        graph,
        latitude,
        longitude,
        get_campus_max_gps_distance(campus_id),
    )
    boundary = get_campus_boundary(campus_id)
    if boundary:
        nearest["within_boundary_polygon"] = point_inside_boundary(
            latitude, longitude, boundary
        )
    return nearest
