from .agent import DeliveryAgent, DeliveryTask
from .costs import road_metrics
from .graph import CampusGraph
from .routing import plan_route


def find_road(
    graph: CampusGraph,
    source: str,
    destination: str
):
    return next(
        (
            road
            for road in graph.adjacency[source]
            if road.destination == destination
        ),
        None
    )


def calculate_battery_usage(
    road,
    priority: str = "NORMAL",
    battery_percentage: float = 100.0,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> float:
    return road_metrics(
        road,
        priority,
        battery_percentage,
        traffic,
        weather
    )["battery_used"]


def simulate_delivery(
    graph: CampusGraph,
    agent: DeliveryAgent,
    task: DeliveryTask,
    block_after_steps: int | None = None,
    road_to_block: tuple[str, str] | None = None,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> dict:

    agent.assign_task(task)

    route_result = plan_route(
        graph=graph,
        start=agent.state.current_location,
        destination=task.destination,
        algorithm="AUTO",
        priority=task.priority,
        battery_percentage=agent.state.battery_percentage,
        traffic=traffic,
        weather=weather
    )

    if not route_result["success"]:
        agent.stop()

        return {
            "success": False,
            "message": "Initial route could not be found."
        }

    current_route = route_result["path"]
    agent.set_route(current_route)

    print("\nDelivery Simulation")
    print("===================")

    agent.display_state()

    print(
        "\nInitial route: "
        + " -> ".join(
            route_result["path_names"]
        )
    )

    step_count = 0
    replanning_count = 0
    blockage_triggered = False

    while (
        agent.state.current_location
        != task.destination
    ):

        if (
            block_after_steps is not None
            and road_to_block is not None
            and step_count == block_after_steps
            and not blockage_triggered
        ):
            graph.block_road(
                road_to_block[0],
                road_to_block[1]
            )
            blockage_triggered = True

            print(
                "\nRoad blocked: "
                f"{road_to_block[0]} -> "
                f"{road_to_block[1]}"
            )

        current_location = (
            agent.state.current_location
        )

        current_route = agent.state.planned_route

        if (
            len(current_route) < 2
            or current_route[0] != current_location
        ):
            replanned = plan_route(
                graph=graph,
                start=current_location,
                destination=task.destination,
                algorithm="AUTO",
                priority=task.priority,
                battery_percentage=agent.state.battery_percentage,
                traffic=traffic,
                weather=weather
            )

            if not replanned["success"]:
                agent.stop()

                return {
                    "success": False,
                    "message": "Re-planning failed.",
                    "replanning_count": replanning_count
                }

            agent.set_route(
                replanned["path"]
            )

            current_route = replanned["path"]
            replanning_count += 1

            print(
                "\nRoute re-planned: "
                + " -> ".join(
                    replanned["path_names"]
                )
            )

        next_location = current_route[1]

        road = find_road(
            graph,
            current_location,
            next_location
        )

        if road is None:
            agent.stop()

            return {
                "success": False,
                "message": "Road information unavailable.",
                "replanning_count": replanning_count
            }

        road_is_blocked = (
            road.blocked
            or (
                road.source,
                road.destination
            ) in graph.blocked_roads
        )

        if road_is_blocked:
            print(
                "\nBlocked road detected. "
                "Re-planning..."
            )

            replanned = plan_route(
                graph=graph,
                start=current_location,
                destination=task.destination,
                algorithm="AUTO",
                priority=task.priority,
                battery_percentage=agent.state.battery_percentage,
                traffic=traffic,
                weather=weather
            )

            if not replanned["success"]:
                agent.stop()

                return {
                    "success": False,
                    "message": "No alternate route available.",
                    "replanning_count": replanning_count
                }

            agent.set_route(
                replanned["path"]
            )

            replanning_count += 1

            print(
                "New route: "
                + " -> ".join(
                    replanned["path_names"]
                )
            )

            continue

        battery_used = calculate_battery_usage(
            road,
            task.priority,
            agent.state.battery_percentage,
            traffic,
            weather
        )

        agent.move_to(
            next_location,
            battery_used
        )

        agent.state.planned_route = (
            agent.state.planned_route[1:]
        )

        print(
            f"\nMoved to: "
            f"{next_location}"
        )

        print(
            f"Battery remaining: "
            f"{agent.state.battery_percentage:.2f}%"
        )

        step_count += 1

        if agent.is_battery_low():
            print(
                "Warning: battery level is low."
            )

    agent.complete_delivery()

    print("\nDelivery completed successfully.")
    agent.display_state()

    return {
        "success": True,
        "message": "Delivery completed.",
        "replanning_count": replanning_count,
        "final_location": agent.state.current_location,
        "remaining_battery": agent.state.battery_percentage
    }
