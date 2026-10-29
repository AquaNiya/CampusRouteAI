from dataclasses import dataclass, field


@dataclass
class DeliveryTask:
    task_id: str
    item_type: str
    pickup_location: str
    destination: str
    priority: str = "NORMAL"


@dataclass
class RobotState:
    robot_id: str
    current_location: str
    battery_percentage: float = 100.0
    carrying_item: str | None = None
    current_task_id: str | None = None
    status: str = "IDLE"
    planned_route: list[str] = field(
        default_factory=list
    )
    completed_deliveries: int = 0


@dataclass
class AgentPercepts:
    current_location: str
    destination: str | None
    nearby_locations: list[str]
    blocked_roads: list[tuple[str, str]]
    battery_percentage: float
    terrain: str | None
    delivery_priority: str


@dataclass
class AgentGoals:
    deliver_item: bool = True
    minimize_route_cost: bool = True
    preserve_battery: bool = True
    avoid_blocked_roads: bool = True
    complete_emergency_delivery_first: bool = True


class DeliveryAgent:

    def __init__(
        self,
        robot_id: str,
        starting_location: str,
        battery_percentage: float = 100.0
    ):
        self.state = RobotState(
            robot_id=robot_id,
            current_location=starting_location,
            battery_percentage=battery_percentage
        )

        self.goals = AgentGoals()

    def perceive(
        self,
        graph,
        destination: str | None,
        priority: str
    ) -> AgentPercepts:

        nearby_roads = graph.get_neighbors(
            self.state.current_location
        )

        nearby_locations = [
            road.destination
            for road in nearby_roads
        ]

        blocked_roads = sorted(
            graph.blocked_roads
        )

        terrain = None

        if nearby_roads:
            terrain = nearby_roads[0].terrain

        return AgentPercepts(
            current_location=self.state.current_location,
            destination=destination,
            nearby_locations=nearby_locations,
            blocked_roads=blocked_roads,
            battery_percentage=self.state.battery_percentage,
            terrain=terrain,
            delivery_priority=priority
        )

    def assign_task(
        self,
        task: DeliveryTask
    ) -> None:

        self.state.current_task_id = task.task_id
        self.state.carrying_item = task.item_type
        self.state.status = "DELIVERY_ASSIGNED"

    def set_route(
        self,
        route: list[str]
    ) -> None:

        self.state.planned_route = route
        self.state.status = "ROUTE_PLANNED"

    def move_to(
        self,
        next_location: str,
        battery_used: float
    ) -> None:

        self.state.current_location = next_location

        self.state.battery_percentage = max(
            0.0,
            self.state.battery_percentage
            - battery_used
        )

        self.state.status = "IN_TRANSIT"

    def complete_delivery(self) -> None:

        self.state.status = "DELIVERED"
        self.state.carrying_item = None
        self.state.current_task_id = None
        self.state.planned_route = []
        self.state.completed_deliveries += 1

    def stop(self) -> None:
        self.state.status = "STOPPED"

    def is_battery_low(
        self,
        threshold: float = 20.0
    ) -> bool:

        return (
            self.state.battery_percentage
            <= threshold
        )

    def display_state(self) -> None:

        print("\nRobot State")
        print("-----------")
        print(
            f"Robot ID: "
            f"{self.state.robot_id}"
        )
        print(
            f"Current location: "
            f"{self.state.current_location}"
        )
        print(
            f"Battery: "
            f"{self.state.battery_percentage:.2f}%"
        )
        print(
            f"Carrying item: "
            f"{self.state.carrying_item or 'Nothing'}"
        )
        print(
            f"Status: "
            f"{self.state.status}"
        )
        print(
            f"Planned route: "
            f"{self.state.planned_route}"
        )


def classify_environment() -> dict[str, str]:

    return {
        "observability": "PARTIALLY_OBSERVABLE",
        "number_of_agents": "SINGLE_AGENT",
        "determinism": "MOSTLY_DETERMINISTIC",
        "episode": "SEQUENTIAL",
        "road_structure": "WEIGHTED",
        "environment_change": "DYNAMIC",
        "task_type": "GOAL_BASED_AND_UTILITY_BASED",
        "map_knowledge": "KNOWN_WITH_DYNAMIC_UPDATES"
    }