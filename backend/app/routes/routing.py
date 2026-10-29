from fastapi import APIRouter, HTTPException

from ..algorithms import a_star, bfs, dfs, dijkstra
from ..map_service import resolve_location
from ..models import RouteRequest
from ..response_models import ApiDict
from ..readiness import enrich_route_result
from ..routing import calculate_metrics, plan_route
from ..runtime import get_graph

router = APIRouter()


def _priority(request: RouteRequest) -> str:
    return "EMERGENCY" if request.emergency else request.priority.upper()


def _locations_or_404(request: RouteRequest):
    graph = get_graph(request.campus_id)
    start = resolve_location(graph, request.start)
    destination = resolve_location(graph, request.destination)
    if start is None:
        raise HTTPException(status_code=404, detail="Starting location not found.")
    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found.")
    return graph, start, destination


@router.post("/api/route", response_model=ApiDict)
def calculate_route(request: RouteRequest) -> dict:
    graph, start, destination = _locations_or_404(request)
    result = plan_route(
        graph=graph,
        start=start.id,
        destination=destination.id,
        algorithm="AUTO",
        priority=_priority(request),
        battery_percentage=request.battery_percentage,
        accessible_only=request.accessible_only,
        traffic=request.traffic,
        weather=request.weather,
    )
    result = enrich_route_result(result)
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])
    return result


@router.post("/api/route/compare", response_model=ApiDict)
def compare_algorithms(request: RouteRequest) -> dict:
    graph, start, destination = _locations_or_404(request)
    priority = _priority(request)
    paths = {
        "BFS": bfs(graph, start.id, destination.id, request.accessible_only),
        "DFS": dfs(graph, start.id, destination.id, request.accessible_only),
        "Dijkstra": dijkstra(
            graph,
            start.id,
            destination.id,
            priority,
            request.battery_percentage,
            request.accessible_only,
            request.traffic,
            request.weather,
        ),
    }
    a_star_result = plan_route(
        graph=graph,
        start=start.id,
        destination=destination.id,
        algorithm="A*",
        priority=priority,
        battery_percentage=request.battery_percentage,
        accessible_only=request.accessible_only,
        traffic=request.traffic,
        weather=request.weather,
    )
    a_star_battery_insufficient = (
        not a_star_result["success"]
        and "battery" in a_star_result.get("message", "").lower()
    )
    if a_star_battery_insufficient:
        paths["A*"] = a_star(
            graph,
            start.id,
            destination.id,
            priority,
            request.battery_percentage,
            request.accessible_only,
            request.traffic,
            request.weather,
        )
    else:
        paths["A*"] = a_star_result.get("path")

    comparison = {}
    for algorithm_name, path in paths.items():
        if path is None:
            comparison[algorithm_name] = {
                "found": False,
                "path": None,
                "battery_insufficient": False,
            }
            continue
        metrics = calculate_metrics(
            graph,
            path,
            request.traffic,
            request.weather,
            priority,
            request.battery_percentage,
        )
        comparison[algorithm_name] = {
            "found": True,
            "path": path,
            "path_names": [graph.locations[item].name for item in path],
            "distance_km": round(metrics["distance_km"], 3),
            "elevation_gain_m": round(metrics["elevation_gain_m"], 2),
            "total_cost": round(metrics["total_cost"], 3),
            "battery_used": round(metrics["battery_used"], 2),
            "battery_insufficient": (
                algorithm_name == "A*"
                and a_star_battery_insufficient
            ),
        }
    return {
        "production_algorithm": "A*",
        "comparison": comparison,
        "battery_insufficient": a_star_battery_insufficient,
    }
