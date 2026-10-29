from backend.app.map_service import (
    find_nearest_location,
    get_available_campuses,
    get_campus_boundary,
    load_campus_graph,
    point_inside_boundary,
)


def test_gps_inside_campus_is_accepted():
    graph = load_campus_graph()

    result = find_nearest_location(
        graph,
        30.3165,
        78.0322
    )

    assert result["within_campus"] is True
    assert result["id"] == "main_gate"


def test_default_campus_is_available():
    campuses = get_available_campuses()

    assert campuses
    assert campuses[0]["id"] == "demo"


def test_gps_outside_campus_is_rejected():
    graph = load_campus_graph()

    result = find_nearest_location(
        graph,
        28.6139,
        77.2090
    )

    assert result["within_campus"] is False


def test_live_boundary_classification():
    boundary = get_campus_boundary()

    assert point_inside_boundary(30.3165, 78.0322, boundary) is True
    assert point_inside_boundary(28.6139, 77.2090, boundary) is False
