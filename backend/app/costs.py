"""Shared travel, energy and routing-cost calculations."""

from typing import TYPE_CHECKING

from .graph import Road

if TYPE_CHECKING:
    from .graph import CampusGraph


TRAFFIC_FACTORS = {
    "NORMAL": 1.0,
    "HEAVY": 1.35,
    "SEVERE": 1.8
}

WEATHER_FACTORS = {
    "CLEAR": 1.0,
    "RAIN": 1.2,
    "STORM": 1.6
}

TERRAIN_FACTORS = {
    "paved": 1.0,
    "gravel": 1.2,
    "mud": 1.5,
    "steep": 1.8
}

TERRAIN_SPEED_KMPH = {
    "paved": 4.5,
    "gravel": 3.5,
    "mud": 2.5,
    "steep": 2.2
}


def _factor(values: dict, value: str, default: float = 1.0) -> float:
    return values.get(value.upper(), default)


def road_metrics(
    road: Road,
    priority: str = "NORMAL",
    battery_percentage: float = 100.0,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> dict[str, float]:
    """Return one consistent metric set used by search, ETA and simulation."""
    terrain_factor = TERRAIN_FACTORS.get(road.terrain.lower(), 1.3)
    terrain_speed = TERRAIN_SPEED_KMPH.get(road.terrain.lower(), 3.0)
    traffic_factor = _factor(TRAFFIC_FACTORS, traffic)
    weather_factor = _factor(WEATHER_FACTORS, weather)

    uphill_energy = max(0.0, road.elevation_gain) * 0.03
    battery_used = (
        road.distance * 2.0 * terrain_factor * weather_factor
        + uphill_energy * weather_factor
    )
    travel_minutes = (
        road.distance / terrain_speed * 60.0
        * traffic_factor
        * weather_factor
    )

    priority_name = priority.upper()
    time_weight = {
        "NORMAL": 0.20,
        "HIGH": 0.45,
        "EMERGENCY": 0.85
    }.get(priority_name, 0.20)
    energy_weight = 1.8 if battery_percentage < 25 else 1.0

    generalized_cost = (
        road.distance * terrain_factor
        + travel_minutes * time_weight
        + battery_used * energy_weight
    )

    return {
        "distance_km": road.distance,
        "elevation_gain_m": max(0.0, road.elevation_gain),
        "battery_used": battery_used,
        "travel_minutes": travel_minutes,
        "generalized_cost": generalized_cost
    }


def road_cost(
    road: Road,
    priority: str = "NORMAL",
    battery_percentage: float = 100.0,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> float:
    return road_metrics(
        road,
        priority,
        battery_percentage,
        traffic,
        weather
    )["generalized_cost"]


def minimum_cost_per_km(
    graph: "CampusGraph",
    priority: str = "NORMAL",
    battery_percentage: float = 100.0,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> float:
    """Return a safe lower-bound cost per kilometre for A*'s heuristic."""
    ratios = []
    for neighbours in graph.adjacency.values():
        for road in neighbours:
            if road.distance <= 0:
                continue
            ratios.append(
                road_cost(
                    road,
                    priority,
                    battery_percentage,
                    traffic,
                    weather
                ) / road.distance
            )

    return min(ratios, default=1.0)
