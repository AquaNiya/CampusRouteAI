from backend.app.costs import minimum_cost_per_km, road_cost, road_metrics
from backend.app.graph import CampusGraph, Location, Road


def make_graph() -> CampusGraph:
    graph = CampusGraph()
    graph.add_location(Location("a", "A", 30.0, 78.0, "POINT", 0))
    graph.add_location(Location("b", "B", 30.0001, 78.0001, "POINT", 10))
    return graph


def test_storm_increases_battery_and_cost():
    road = Road("a", "b", 1.0, 10, "paved", True, False)
    clear = road_metrics(road, traffic="NORMAL", weather="CLEAR")
    storm = road_metrics(road, traffic="SEVERE", weather="STORM")

    assert storm["battery_used"] > clear["battery_used"]
    assert storm["travel_minutes"] > clear["travel_minutes"]
    assert storm["generalized_cost"] > clear["generalized_cost"]


def test_road_cost_matches_shared_metric():
    road = Road("a", "b", 1.0, 0, "gravel", True, False)
    metrics = road_metrics(road, priority="HIGH", battery_percentage=20)

    assert road_cost(road, "HIGH", 20) == metrics["generalized_cost"]


def test_minimum_cost_per_km_is_positive():
    graph = make_graph()
    graph.add_road(Road("a", "b", 1.0, 10, "paved", True, False))

    assert minimum_cost_per_km(graph) > 0
