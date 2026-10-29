from .agent import DeliveryAgent, DeliveryTask, classify_environment
from .map_service import find_nearest_location, load_campus_graph, resolve_location
from .simulation import simulate_delivery


def display_environment() -> None:
    print("\nAgent Environment")
    print("=================")

    environment = classify_environment()

    for property_name, value in environment.items():
        formatted_name = property_name.replace(
            "_",
            " "
        ).title()

        print(
            f"{formatted_name}: {value}"
        )


def display_locations(graph) -> None:
    print("\nAvailable locations")
    print("===================")

    for location in graph.locations.values():
        print(
            f"{location.id} - "
            f"{location.name}"
        )


def choose_location(
    graph,
    message: str
) -> str:

    while True:
        value = input(
            f"\n{message}: "
        ).strip()

        location = resolve_location(
            graph,
            value
        )

        if location is not None:
            return location.id

        print(
            "Location not found. "
            "Enter a valid ID or exact name."
        )


def choose_start_from_gps(graph) -> str:

    try:
        latitude = float(
            input("Enter latitude: ")
        )

        longitude = float(
            input("Enter longitude: ")
        )

    except ValueError:
        print(
            "Invalid coordinates. "
            "Using manual selection."
        )

        return choose_location(
            graph,
            "Enter starting location"
        )

    nearest = find_nearest_location(
        graph,
        latitude,
        longitude
    )

    print(
        f"Detected location: "
        f"{nearest['name']}"
    )

    return nearest["id"]


def main() -> None:

    graph = load_campus_graph()

    print("CampusRoute AI")
    print("==============")

    display_environment()
    display_locations(graph)

    print("\n1. Select starting location")
    print("2. Use GPS coordinates")

    start_mode = input(
        "Choose option: "
    ).strip()

    if start_mode == "2":
        start = choose_start_from_gps(graph)
    else:
        start = choose_location(
            graph,
            "Enter starting location"
        )

    destination = choose_location(
        graph,
        "Enter destination"
    )

    item_type = input(
        "\nItem type "
        "(BOOK/MEDICINE/DOCUMENT/FOOD): "
    ).strip().upper()

    priority = input(
        "Priority "
        "(NORMAL/HIGH/EMERGENCY): "
    ).strip().upper()

    if priority not in {
        "NORMAL",
        "HIGH",
        "EMERGENCY"
    }:
        priority = "NORMAL"

    traffic = input(
        "Traffic (NORMAL/HEAVY/SEVERE): "
    ).strip().upper()

    if traffic not in {"NORMAL", "HEAVY", "SEVERE"}:
        traffic = "NORMAL"

    weather = input(
        "Weather (CLEAR/RAIN/STORM): "
    ).strip().upper()

    if weather not in {"CLEAR", "RAIN", "STORM"}:
        weather = "CLEAR"

    try:
        battery = float(
            input("Robot battery percentage: ")
        )

    except ValueError:
        battery = 100.0

    battery = max(
        0.0,
        min(100.0, battery)
    )

    simulate_blockage = input(
        "Simulate blocked road? (y/n): "
    ).strip().lower()

    block_after_steps = None
    road_to_block = None

    if simulate_blockage == "y":
        try:
            block_after_steps = int(
                input(
                    "Block road after how many moves? "
                )
            )

        except ValueError:
            block_after_steps = 1

        blocked_source = choose_location(
            graph,
            "Enter blocked road source"
        )

        blocked_destination = choose_location(
            graph,
            "Enter blocked road destination"
        )

        road_to_block = (
            blocked_source,
            blocked_destination
        )

    task = DeliveryTask(
        task_id="TASK-001",
        item_type=item_type,
        pickup_location=start,
        destination=destination,
        priority=priority
    )

    agent = DeliveryAgent(
        robot_id="ROBOT-001",
        starting_location=start,
        battery_percentage=battery
    )

    simulate_delivery(
        graph=graph,
        agent=agent,
        task=task,
        block_after_steps=block_after_steps,
        road_to_block=road_to_block,
        traffic=traffic,
        weather=weather
    )


if __name__ == "__main__":
    main()
