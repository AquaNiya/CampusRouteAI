from backend.app.agent import DeliveryAgent, DeliveryTask, classify_environment


def test_environment_classification_covers_ai_properties():
    environment = classify_environment()

    assert environment["observability"] == "PARTIALLY_OBSERVABLE"
    assert environment["number_of_agents"] == "SINGLE_AGENT"
    assert environment["episode"] == "SEQUENTIAL"
    assert environment["road_structure"] == "WEIGHTED"
    assert environment["environment_change"] == "DYNAMIC"


def test_agent_state_changes_during_delivery():
    agent = DeliveryAgent("ROBOT-001", "main_gate", 80)
    task = DeliveryTask(
        "TASK-001",
        "MEDICINE",
        "main_gate",
        "medical_centre",
        "EMERGENCY"
    )

    agent.assign_task(task)
    assert agent.state.status == "DELIVERY_ASSIGNED"
    assert agent.state.carrying_item == "MEDICINE"

    agent.set_route(["main_gate", "south_parking", "medical_centre"])
    agent.move_to("south_parking", 1.0)

    assert agent.state.current_location == "south_parking"
    assert agent.state.battery_percentage == 79
    assert agent.state.planned_route[0] == "main_gate"

    agent.complete_delivery()
    assert agent.state.status == "DELIVERED"
    assert agent.state.carrying_item is None
