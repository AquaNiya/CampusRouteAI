import json
from pathlib import Path

import pytest

from backend.app.graph import CampusGraph

CAMPUS_FILE = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "app"
    / "campus.json"
)


def test_campus_graph_loads():
    graph = CampusGraph.from_json(CAMPUS_FILE)

    assert len(graph.locations) > 0
    assert "main_gate" in graph.locations
    assert "medical_centre" in graph.locations


def test_graph_has_roads():
    graph = CampusGraph.from_json(CAMPUS_FILE)

    neighbours = graph.get_neighbors(
        "main_gate"
    )

    assert len(neighbours) > 0


def test_blocked_road_is_not_available():
    graph = CampusGraph.from_json(CAMPUS_FILE)

    graph.block_road(
        "main_gate",
        "south_parking"
    )

    neighbours = graph.get_neighbors(
        "main_gate"
    )

    neighbour_ids = [
        road.destination
        for road in neighbours
    ]

    assert "south_parking" not in neighbour_ids


def test_nearest_location():
    graph = CampusGraph.from_json(CAMPUS_FILE)

    nearest = graph.nearest_location(
        30.3165,
        78.0322
    )

    assert nearest.id == "main_gate"


def test_map_rejects_road_shorter_than_straight_line(tmp_path):
    map_data = {
        "locations": [
            {
                "id": "a",
                "name": "A",
                "latitude": 30.0,
                "longitude": 78.0,
                "type": "POINT",
                "elevation": 0
            },
            {
                "id": "b",
                "name": "B",
                "latitude": 30.01,
                "longitude": 78.0,
                "type": "POINT",
                "elevation": 0
            }
        ],
        "roads": [
            {
                "from": "a",
                "to": "b",
                "distance": 0.1
            }
        ]
    }
    map_file = tmp_path / "invalid.json"
    map_file.write_text(json.dumps(map_data), encoding="utf-8")

    with pytest.raises(ValueError, match="shorter than straight-line distance"):
        CampusGraph.from_json(map_file)


def test_campus_elevation_gain_matches_node_elevations():
    data = json.loads(CAMPUS_FILE.read_text(encoding="utf-8"))
    elevations = {
        location["id"]: location["elevation"]
        for location in data["locations"]
    }

    for road in data["roads"]:
        expected = max(
            0,
            elevations[road["to"]] - elevations[road["from"]]
        )
        assert road["elevation_gain"] == expected, (
            f"Elevation mismatch for {road['from']} -> {road['to']}"
        )
