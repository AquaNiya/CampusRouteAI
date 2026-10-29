from .agent import DeliveryTask
from .map_service import load_campus_graph, resolve_location
from .optimization import optimize_deliveries


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
            "Enter a valid ID or name."
        )


def choose_priority() -> str:

    priority = input(
        "Priority "
        "(NORMAL/HIGH/EMERGENCY): "
    ).strip().upper()

    if priority not in {
        "NORMAL",
        "HIGH",
        "EMERGENCY"
    }:
        return "NORMAL"

    return priority


def main() -> None:

    graph = load_campus_graph()

    print("Multiple Delivery Optimizer")
    print("===========================")

    starting_location = choose_location(
        graph,
        "Enter robot starting location"
    )

    try:
        task_count = int(
            input(
                "How many deliveries? "
            )
        )

    except ValueError:
        task_count = 2

    task_count = max(
        1,
        min(5, task_count)
    )

    tasks = []

    for index in range(1, task_count + 1):
        print(f"\nDelivery {index}")

        pickup_location = choose_location(
            graph,
            "Enter pickup location"
        )

        destination = choose_location(
            graph,
            "Enter destination"
        )

        item_type = input(
            "Item type: "
        ).strip().upper()

        priority = choose_priority()

        task = DeliveryTask(
            task_id=f"TASK-{index:03d}",
            item_type=item_type,
            pickup_location=pickup_location,
            destination=destination,
            priority=priority
        )

        tasks.append(task)

    try:
        battery = float(
            input(
                "\nRobot battery percentage: "
            )
        )

    except ValueError:
        battery = 100.0

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

    result = optimize_deliveries(
        graph=graph,
        starting_location=starting_location,
        tasks=tasks,
        battery_percentage=battery,
        traffic=traffic,
        weather=weather
    )

    print("\nOptimization Result")
    print("===================")

    if not result["success"]:
        print(result["message"])
        return

    print(
        "Optimized task order: "
        + " -> ".join(
            result["task_order"]
        )
    )

    print("\nDelivery sequence:")

    for task_id, destination_id in zip(
        result["task_order"],
        result["task_destinations"]
    ):
        destination_name = graph.locations[
            destination_id
        ].name

        print(
            f"{task_id} -> {destination_name}"
        )

    print("\nCombined route:")

    route_names = [
        graph.locations[location_id].name
        for location_id in result["combined_route"]
    ]

    print(
        " -> ".join(route_names)
    )

    print(
        f"\nTotal distance: "
        f"{result['total_distance']} km"
    )

    print(
        f"Estimated battery used: "
        f"{result['battery_used']}%"
    )

    print(
        f"Estimated time: "
        f"{result['estimated_time_minutes']} minutes"
    )


if __name__ == "__main__":
    main()
