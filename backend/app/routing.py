import itertools
from collections.abc import Callable
from dataclasses import dataclass

from .algorithms import a_star, bfs, dfs, dijkstra
from .costs import road_metrics
from .graph import CampusGraph


@dataclass(frozen=True)
class RoutingDecision:
    algorithm: str
    strategy: str
    reason: str


def _strategy_for(
    algorithm: str,
    priority: str,
    battery_percentage: float,
    accessible_only: bool
) -> str:
    if algorithm == "DIJKSTRA" and battery_percentage < 25:
        return "ENERGY_AWARE_DIJKSTRA"

    if accessible_only:
        return "ACCESSIBLE_A_STAR"

    if priority.upper() == "EMERGENCY":
        return "EMERGENCY_A_STAR"

    if priority.upper() == "HIGH":
        return "HIGH_PRIORITY_A_STAR"

    return "BALANCED_A_STAR"


def choose_strategy(
    priority: str,
    battery_percentage: float,
    accessible_only: bool
) -> str:
    algorithm = "DIJKSTRA" if battery_percentage < 25 and priority.upper() != "EMERGENCY" else "A*"
    return _strategy_for(
        algorithm,
        priority,
        battery_percentage,
        accessible_only
    )


def _is_uniform_unweighted_graph(
    graph: CampusGraph
) -> bool:
    roads = [
        road
        for neighbours in graph.adjacency.values()
        for road in neighbours
        if not road.blocked
    ]

    if not roads:
        return False

    first_distance = roads[0].distance

    return all(
        abs(road.distance - first_distance) < 1e-9
        and road.elevation_gain == 0
        and road.terrain.lower() == "paved"
        for road in roads
    )


def choose_algorithm(
    graph: CampusGraph,
    priority: str,
    battery_percentage: float,
    accessible_only: bool
) -> tuple[str, str]:
    """Choose an algorithm based on graph and delivery conditions."""

    decision = choose_routing_decision(
        graph,
        priority,
        battery_percentage,
        accessible_only
    )
    return decision.algorithm, decision.reason


def choose_routing_decision(
    graph: CampusGraph,
    priority: str,
    battery_percentage: float,
    accessible_only: bool
) -> RoutingDecision:
    priority_name = priority.upper()

    if priority_name == "EMERGENCY":
        return RoutingDecision(
            "A*",
            "EMERGENCY_A_STAR",
            "A* is retained for emergency delivery because response time is "
            "the primary objective; battery feasibility is checked separately."
        )

    if battery_percentage < 25:
        return RoutingDecision(
            "DIJKSTRA",
            "ENERGY_AWARE_DIJKSTRA",
            "Dijkstra was selected because the remaining battery is low and "
            "the weighted energy cost must be minimised."
        )

    if (
        _is_uniform_unweighted_graph(graph)
        and priority.upper() == "NORMAL"
        and not accessible_only
    ):
        return RoutingDecision(
            "BFS",
            "BALANCED_BFS",
            "BFS was selected because every usable road has equal cost."
        )

    if accessible_only:
        return RoutingDecision(
            "A*",
            "ACCESSIBLE_A_STAR",
            "A* was selected after inaccessible roads were filtered out."
        )

    if priority_name == "HIGH":
        return RoutingDecision(
            "A*",
            "HIGH_PRIORITY_A_STAR",
            "A* was selected because this weighted route should reduce travel time."
        )

    return RoutingDecision(
        "A*",
        "BALANCED_A_STAR",
        "A* was selected because the campus graph is weighted and GPS "
        "coordinates provide a goal-directed heuristic."
    )


def _search(
    graph: CampusGraph,
    algorithm: str,
    start: str,
    destination: str,
    priority: str,
    battery_percentage: float,
    accessible_only: bool,
    traffic: str,
    weather: str
) -> list[str] | None:
    searches: dict[str, Callable[..., list[str] | None]] = {
        "BFS": bfs,
        "DFS": dfs,
        "DIJKSTRA": dijkstra,
        "A*": a_star
    }

    search = searches[algorithm]

    if algorithm in {"BFS", "DFS"}:
        return search(
            graph,
            start,
            destination,
            accessible_only
        )

    return search(
        graph,
        start,
        destination,
        priority,
        battery_percentage,
        accessible_only,
        traffic,
        weather
    )


def _algorithm_analysis(
    graph: CampusGraph,
    start: str,
    destination: str,
    priority: str,
    battery_percentage: float,
    accessible_only: bool,
    selected_algorithm: str,
    traffic: str,
    weather: str
) -> dict:
    notes = {
        "BFS": "Shortest by number of edges; not cost-optimal on weighted roads.",
        "DFS": "Useful for exploration; does not guarantee a shortest route.",
        "DIJKSTRA": "Least-cost weighted route without a heuristic.",
        "A*": "Least-cost goal-directed route using GPS distance as heuristic."
    }
    analysis = {}

    for algorithm in ("BFS", "DFS", "DIJKSTRA", "A*"):
        path = _search(
            graph,
            algorithm,
            start,
            destination,
            priority,
            battery_percentage,
            accessible_only,
            traffic,
            weather
        )

        if path is None:
            analysis[algorithm] = {
                "found": False,
                "selected": algorithm == selected_algorithm,
                "note": notes[algorithm]
            }
            continue

        metrics = calculate_metrics(
            graph,
            path,
            traffic,
            weather,
            priority,
            battery_percentage
        )
        analysis[algorithm] = {
            "found": True,
            "selected": algorithm == selected_algorithm,
            "path": path,
            "path_names": [
                graph.locations[location_id].name
                for location_id in path
            ],
            "distance_km": round(metrics["distance_km"], 3),
            "elevation_gain_m": round(
                metrics["elevation_gain_m"],
                2
            ),
            "battery_used": round(metrics["battery_used"], 2),
            "estimated_time_minutes": metrics["estimated_time_minutes"],
            "total_cost": round(metrics["total_cost"], 3),
            "note": notes[algorithm]
        }

    return analysis


def plan_route(
    graph: CampusGraph,
    start: str,
    destination: str,
    algorithm: str = "AUTO",
    priority: str = "NORMAL",
    battery_percentage: float = 100.0,
    accessible_only: bool = False,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> dict:
    decision = choose_routing_decision(
        graph,
        priority,
        battery_percentage,
        accessible_only
    )
    automatic_algorithm = decision.algorithm
    selection_reason = decision.reason

    requested_algorithm = algorithm.upper()

    if requested_algorithm == "AUTO":
        selected_algorithm = automatic_algorithm
    elif requested_algorithm in {"BFS", "DFS", "DIJKSTRA", "A*"}:
        selected_algorithm = requested_algorithm
        selection_reason = (
            f"{selected_algorithm} was explicitly requested for comparison."
        )
    else:
        selected_algorithm = automatic_algorithm

    path = _search(
        graph,
        selected_algorithm,
        start,
        destination,
        priority,
        battery_percentage,
        accessible_only,
        traffic,
        weather
    )

    strategy = _strategy_for(
        selected_algorithm,
        priority,
        battery_percentage,
        accessible_only
    )

    if path is None:
        return {
            "success": False,
            "message": "No feasible route found.",
            "algorithm": selected_algorithm,
            "strategy": strategy,
            "selection_reason": selection_reason
        }

    metrics = calculate_metrics(
        graph,
        path,
        traffic,
        weather,
        priority,
        battery_percentage
    )
    remaining_battery = battery_percentage - metrics["battery_used"]

    if remaining_battery < 0:
        return {
            "success": False,
            "message": (
                "Battery is insufficient for this route. "
                "Recharge the robot or choose a closer destination."
            ),
            "algorithm": selected_algorithm,
            "strategy": strategy,
            "battery_required": round(metrics["battery_used"], 2),
            "battery_available": round(battery_percentage, 2),
            "selection_reason": selection_reason
        }

    return {
        "success": True,
        "algorithm": selected_algorithm,
        "strategy": strategy,
        "selection_reason": selection_reason,
        "path": path,
        "path_names": [
            graph.locations[location_id].name
            for location_id in path
        ],
        "distance_km": round(metrics["distance_km"], 3),
        "elevation_gain_m": round(metrics["elevation_gain_m"], 2),
        "battery_used": round(metrics["battery_used"], 2),
        "total_cost": round(metrics["total_cost"], 3),
        "remaining_battery": round(remaining_battery, 2),
        "battery_warning": remaining_battery < 10,
        "battery_feasible": True,
        "priority": priority.upper(),
        "traffic": traffic.upper(),
        "weather": weather.upper(),
        "estimated_time_minutes": metrics["estimated_time_minutes"],
        "delay_reasons": metrics["delay_reasons"],
        "algorithm_analysis": _algorithm_analysis(
            graph,
            start,
            destination,
            priority,
            battery_percentage,
            accessible_only,
            selected_algorithm,
            traffic,
            weather
        )
    }


def calculate_metrics(
    graph: CampusGraph,
    path: list[str],
    traffic: str = "NORMAL",
    weather: str = "CLEAR",
    priority: str = "NORMAL",
    battery_percentage: float = 100.0
) -> dict:
    distance = 0.0
    elevation_gain = 0.0
    estimated_time = 0.0
    battery_used = 0.0
    total_cost = 0.0
    delay_reasons = []

    for first, second in itertools.pairwise(path):
        road = next(
            (
                road
                for road in graph.adjacency[first]
                if road.destination == second
            ),
            None
        )

        if road is None:
            raise ValueError(f"Road not found: {first} -> {second}")

        metrics = road_metrics(
            road,
            priority=priority,
            battery_percentage=battery_percentage,
            traffic=traffic,
            weather=weather
        )
        distance += metrics["distance_km"]
        elevation_gain += metrics["elevation_gain_m"]
        estimated_time += metrics["travel_minutes"]
        battery_used += metrics["battery_used"]
        total_cost += metrics["generalized_cost"]

    if traffic.upper() != "NORMAL":
        delay_reasons.append(
            f"{traffic.title()} traffic increased travel time."
        )

    if weather.upper() != "CLEAR":
        delay_reasons.append(
            f"{weather.title()} weather reduced movement speed."
        )

    if elevation_gain > 0:
        delay_reasons.append(
            "Elevation gain added uphill travel time."
        )

    return {
        "distance_km": distance,
        "elevation_gain_m": elevation_gain,
        "battery_used": battery_used,
        "total_cost": total_cost,
        "estimated_time_minutes": max(
            1,
            round(estimated_time)
        ),
        "delay_reasons": delay_reasons
    }
