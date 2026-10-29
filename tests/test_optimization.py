from pathlib import Path

from backend.app.agent import DeliveryTask
from backend.app.graph import CampusGraph
from backend.app.optimization import optimize_deliveries

CAMPUS_FILE = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "app"
    / "campus.json"
)


def test_multiple_delivery_optimizer_returns_feasible_order():
    graph = CampusGraph.from_json(CAMPUS_FILE)
    tasks = [
        DeliveryTask(
            "TASK-001",
            "MEDICINE",
            "main_gate",
            "medical_centre",
            "EMERGENCY"
        ),
        DeliveryTask(
            "TASK-002",
            "DOCUMENT",
            "academic_block",
            "girls_hostel",
            "NORMAL"
        )
    ]

    result = optimize_deliveries(
        graph,
        "main_gate",
        tasks,
        89
    )

    assert result["success"] is True
    assert result["task_order"] == ["TASK-001", "TASK-002"]
    assert result["total_distance"] > 0
    assert result["battery_used"] > 0


def test_optimizer_rejects_empty_tasks():
    graph = CampusGraph.from_json(CAMPUS_FILE)

    result = optimize_deliveries(
        graph,
        "main_gate",
        [],
        90
    )

    assert result["success"] is False


def test_optimizer_allows_interleaved_pickups_and_returns_reason():
    graph = CampusGraph.from_json(CAMPUS_FILE)
    tasks = [
        DeliveryTask(
            "TASK-A",
            "DOCUMENT",
            "main_gate",
            "girls_hostel",
            "NORMAL"
        ),
        DeliveryTask(
            "TASK-B",
            "MEDICINE",
            "academic_block",
            "medical_centre",
            "HIGH"
        )
    ]

    result = optimize_deliveries(graph, "main_gate", tasks, 80)

    assert result["success"] is True
    assert result["planning_method"] == "brute-force precedence search"
    assert result["total_cost"] > 0
    assert result["why_order"]
    first_drop = next(
        index
        for index, stop in enumerate(result["stop_order"])
        if stop.startswith("DROP:")
    )
    assert first_drop > 1


def test_optimizer_honours_high_priority_as_weighted_cost():
    graph = CampusGraph.from_json(CAMPUS_FILE)
    tasks = [
        DeliveryTask(
            "NORMAL-TASK",
            "DOCUMENT",
            "south_parking",
            "girls_hostel",
            "NORMAL"
        ),
        DeliveryTask(
            "HIGH-TASK",
            "MEDICINE",
            "main_gate",
            "medical_centre",
            "HIGH"
        )
    ]

    result = optimize_deliveries(graph, "main_gate", tasks, 80)

    assert result["success"] is True
    assert result["task_order"][0] == "HIGH-TASK"
    assert result["priority_penalty"] >= 0


def test_optimizer_rejects_batch_when_running_battery_is_insufficient():
    graph = CampusGraph.from_json(CAMPUS_FILE)
    tasks = [
        DeliveryTask(
            "TASK-001",
            "MEDICINE",
            "main_gate",
            "medical_centre",
            "EMERGENCY"
        ),
        DeliveryTask(
            "TASK-002",
            "DOCUMENT",
            "academic_block",
            "girls_hostel",
            "NORMAL"
        )
    ]

    result = optimize_deliveries(graph, "main_gate", tasks, 2)

    assert result["success"] is False
    assert "battery" in result["message"].lower()
