from pathlib import Path

from backend.app.graph import CampusGraph, Location, Road
from backend.app.routing import plan_route

CAMPUS_FILE = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "app"
    / "campus.json"
)


def create_graph() -> CampusGraph:
    return CampusGraph.from_json(
        CAMPUS_FILE
    )


def create_competing_route_graph() -> CampusGraph:
    graph = CampusGraph()
    locations = [
        Location("start", "Start", 30.00000, 78.00000, "POINT", 0),
        Location("mud_mid", "Mud shortcut", 30.00005, 78.00005, "POINT", 0),
        Location("paved_mid", "Paved detour", 30.00005, 78.00020, "POINT", 0),
        Location("goal", "Goal", 30.00010, 78.00010, "POINT", 0)
    ]
    for location in locations:
        graph.add_location(location)

    roads = [
        Road("start", "mud_mid", 0.5, 0, "mud", True, False),
        Road("mud_mid", "goal", 0.5, 0, "mud", True, False),
        Road("start", "paved_mid", 0.83, 0, "paved", True, False),
        Road("paved_mid", "goal", 0.83, 0, "paved", True, False)
    ]
    for road in roads:
        graph.add_road(road)
        graph.add_road(
            Road(
                road.destination,
                road.source,
                road.distance,
                road.elevation_gain,
                road.terrain,
                road.accessible,
                road.blocked
            )
        )
    return graph


def test_normal_route():
    graph = create_graph()

    result = plan_route(
        graph=graph,
        start="main_gate",
        destination="medical_centre",
        algorithm="A*",
        priority="NORMAL",
        battery_percentage=80
    )

    assert result["success"] is True
    assert result["algorithm"] == "A*"
    assert result["strategy"] == "BALANCED_A_STAR"
    assert result["distance_km"] > 0


def test_emergency_route():
    graph = create_graph()

    result = plan_route(
        graph=graph,
        start="main_gate",
        destination="medical_centre",
        algorithm="A*",
        priority="EMERGENCY",
        battery_percentage=80
    )

    assert result["success"] is True
    assert result["strategy"] == "EMERGENCY_A_STAR"
    assert result["priority"] == "EMERGENCY"


def test_high_priority_strategy():
    graph = create_graph()

    result = plan_route(
        graph=graph,
        start="main_gate",
        destination="medical_centre",
        algorithm="A*",
        priority="HIGH",
        battery_percentage=80
    )

    assert result["success"] is True
    assert result["strategy"] == "HIGH_PRIORITY_A_STAR"
    assert result["priority"] == "HIGH"


def test_low_battery_strategy():
    graph = create_graph()

    result = plan_route(
        graph=graph,
        start="main_gate",
        destination="girls_hostel",
        algorithm="AUTO",
        priority="NORMAL",
        battery_percentage=15
    )

    assert result["success"] is True
    assert result["strategy"] == "ENERGY_AWARE_DIJKSTRA"
    assert result["algorithm"] == "DIJKSTRA"


def test_auto_selects_dijkstra_for_low_battery():
    graph = create_graph()

    result = plan_route(
        graph=graph,
        start="main_gate",
        destination="girls_hostel",
        algorithm="AUTO",
        priority="NORMAL",
        battery_percentage=30
    )

    assert result["success"] is True
    assert result["algorithm"] == "A*"

    low_battery_result = plan_route(
        graph=graph,
        start="main_gate",
        destination="girls_hostel",
        algorithm="AUTO",
        priority="NORMAL",
        battery_percentage=15
    )

    assert low_battery_result["algorithm"] == "DIJKSTRA"


def test_accessible_strategy():
    graph = create_graph()

    result = plan_route(
        graph=graph,
        start="main_gate",
        destination="girls_hostel",
        algorithm="A*",
        priority="NORMAL",
        battery_percentage=80,
        accessible_only=True
    )

    assert result["success"] is True
    assert result["strategy"] == "ACCESSIBLE_A_STAR"


def test_route_after_blockage():
    graph = create_graph()

    graph.block_road(
        "main_gate",
        "south_parking"
    )

    result = plan_route(
        graph=graph,
        start="main_gate",
        destination="medical_centre",
        algorithm="A*",
        priority="NORMAL",
        battery_percentage=80
    )

    assert result["success"] is True
    assert "south_parking" not in result["path"]


def test_route_fails_when_battery_is_insufficient():
    graph = create_graph()

    result = plan_route(
        graph=graph,
        start="main_gate",
        destination="medical_centre",
        algorithm="A*",
        priority="NORMAL",
        battery_percentage=1
    )

    assert result["success"] is False
    assert "Battery is insufficient" in result["message"]


def test_conditions_change_eta_and_explain_delays():
    graph = create_graph()

    clear_route = plan_route(
        graph=graph,
        start="main_gate",
        destination="medical_centre",
        algorithm="AUTO",
        priority="NORMAL",
        battery_percentage=80,
        traffic="NORMAL",
        weather="CLEAR"
    )
    difficult_route = plan_route(
        graph=graph,
        start="main_gate",
        destination="medical_centre",
        algorithm="AUTO",
        priority="NORMAL",
        battery_percentage=80,
        traffic="SEVERE",
        weather="STORM"
    )

    assert difficult_route["estimated_time_minutes"] > clear_route[
        "estimated_time_minutes"
    ]
    assert difficult_route["delay_reasons"]
    assert difficult_route["total_cost"] > clear_route["total_cost"]


def test_emergency_low_battery_decision_is_consistent():
    graph = create_graph()

    result = plan_route(
        graph=graph,
        start="main_gate",
        destination="medical_centre",
        algorithm="AUTO",
        priority="EMERGENCY",
        battery_percentage=20
    )

    assert result["algorithm"] == "A*"
    assert result["strategy"] == "EMERGENCY_A_STAR"


def test_reverse_edge_does_not_charge_uphill_energy():
    graph = create_graph()

    reverse_road = next(
        road
        for road in graph.adjacency["academic_block"]
        if road.destination == "main_gate"
    )

    assert reverse_road.elevation_gain == 0


def test_severe_traffic_changes_competing_route():
    graph = create_competing_route_graph()

    clear = plan_route(
        graph,
        "start",
        "goal",
        traffic="NORMAL",
        weather="CLEAR",
        battery_percentage=80
    )
    severe = plan_route(
        graph,
        "start",
        "goal",
        traffic="SEVERE",
        weather="CLEAR",
        battery_percentage=80
    )

    assert clear["path"] != severe["path"]
    assert clear["total_cost"] != severe["total_cost"]
