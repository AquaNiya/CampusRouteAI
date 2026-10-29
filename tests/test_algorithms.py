from pathlib import Path

from backend.app.algorithms import a_star, bfs, dfs
from backend.app.graph import CampusGraph

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


def test_bfs_finds_route():
    graph = create_graph()

    route = bfs(
        graph,
        "main_gate",
        "medical_centre"
    )

    assert route is not None
    assert route[0] == "main_gate"
    assert route[-1] == "medical_centre"


def test_dfs_finds_route():
    graph = create_graph()

    route = dfs(
        graph,
        "main_gate",
        "medical_centre"
    )

    assert route is not None
    assert route[0] == "main_gate"
    assert route[-1] == "medical_centre"


def test_a_star_finds_route():
    graph = create_graph()

    route = a_star(
        graph,
        "main_gate",
        "medical_centre",
        priority="EMERGENCY",
        battery_percentage=80
    )

    assert route is not None
    assert route[0] == "main_gate"
    assert route[-1] == "medical_centre"


def test_a_star_avoids_blocked_road():
    graph = create_graph()

    graph.block_road(
        "main_gate",
        "south_parking"
    )

    route = a_star(
        graph,
        "main_gate",
        "medical_centre"
    )

    assert route is not None
    assert route[0] == "main_gate"
    assert route[-1] == "medical_centre"
    assert "south_parking" not in route


def test_accessible_route_avoids_inaccessible_road():
    graph = create_graph()

    route = a_star(
        graph,
        "north_parking",
        "girls_hostel",
        accessible_only=True
    )

    assert route is not None
    assert route[0] == "north_parking"
    assert route[-1] == "girls_hostel"