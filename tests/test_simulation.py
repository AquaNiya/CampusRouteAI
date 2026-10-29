from pathlib import Path

from backend.app.agent import DeliveryAgent, DeliveryTask
from backend.app.graph import CampusGraph
from backend.app.simulation import simulate_delivery

CAMPUS_FILE = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "app"
    / "campus.json"
)


def test_simulation_replans_after_blockage():
    graph = CampusGraph.from_json(CAMPUS_FILE)
    agent = DeliveryAgent("ROBOT-001", "main_gate", 80)
    task = DeliveryTask(
        "TASK-001",
        "MEDICINE",
        "main_gate",
        "medical_centre",
        "EMERGENCY"
    )

    result = simulate_delivery(
        graph,
        agent,
        task,
        block_after_steps=0,
        road_to_block=("main_gate", "south_parking")
    )

    assert result["success"] is True
    assert result["replanning_count"] >= 1
    assert result["final_location"] == "medical_centre"
