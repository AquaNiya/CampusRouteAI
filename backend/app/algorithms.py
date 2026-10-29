import heapq
from collections import deque

from .costs import minimum_cost_per_km, road_cost
from .graph import CampusGraph


def bfs(
    graph: CampusGraph,
    start: str,
    goal: str,
    accessible_only: bool = False
) -> list[str] | None:

    if start not in graph.locations:
        return None

    if goal not in graph.locations:
        return None

    queue = deque([start])
    visited = {start}
    parent: dict[str, str | None] = {
        start: None
    }

    while queue:
        current = queue.popleft()

        if current == goal:
            return build_path(parent, goal)

        for road in graph.get_neighbors(
            current,
            accessible_only
        ):
            neighbour = road.destination

            if neighbour in visited:
                continue

            visited.add(neighbour)
            parent[neighbour] = current
            queue.append(neighbour)

    return None


def dfs(
    graph: CampusGraph,
    start: str,
    goal: str,
    accessible_only: bool = False
) -> list[str] | None:

    if start not in graph.locations:
        return None

    if goal not in graph.locations:
        return None

    stack = [start]
    visited = set()
    parent: dict[str, str | None] = {
        start: None
    }

    while stack:
        current = stack.pop()

        if current in visited:
            continue

        visited.add(current)

        if current == goal:
            return build_path(parent, goal)

        neighbours = graph.get_neighbors(
            current,
            accessible_only
        )

        for road in reversed(neighbours):
            neighbour = road.destination

            if neighbour not in visited:
                parent[neighbour] = current
                stack.append(neighbour)

    return None


def a_star(
    graph: CampusGraph,
    start: str,
    goal: str,
    priority: str = "NORMAL",
    battery_percentage: float = 100.0,
    accessible_only: bool = False,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> list[str] | None:

    if start not in graph.locations:
        return None

    if goal not in graph.locations:
        return None

    heuristic_scale = minimum_cost_per_km(
        graph,
        priority,
        battery_percentage,
        traffic,
        weather
    )
    open_set = [(0.0, 0.0, start)]
    parent: dict[str, str | None] = {
        start: None
    }
    cost_so_far = {
        start: 0.0
    }

    while open_set:
        _, current_cost, current = heapq.heappop(open_set)

        if current_cost > cost_so_far[current]:
            continue

        if current == goal:
            return build_path(parent, goal)

        for road in graph.get_neighbors(
            current,
            accessible_only
        ):
            next_cost = (
                cost_so_far[current]
                + road_cost(
                    road,
                    priority,
                    battery_percentage,
                    traffic,
                    weather
                )
            )

            neighbour = road.destination

            if (
                neighbour not in cost_so_far
                or next_cost < cost_so_far[neighbour]
            ):
                cost_so_far[neighbour] = next_cost
                parent[neighbour] = current

                heuristic = scaled_heuristic(
                    graph,
                    neighbour,
                    goal,
                    heuristic_scale
                )

                heapq.heappush(
                    open_set,
                    (
                        next_cost + heuristic,
                        next_cost,
                        neighbour
                    )
                )

    return None


def scaled_heuristic(
    graph: CampusGraph,
    node: str,
    goal: str,
    cost_per_km: float | None = None
) -> float:
    """Estimate remaining cost using distance and the map's safe lower bound."""
    scale = cost_per_km
    if scale is None:
        scale = minimum_cost_per_km(graph)
    return graph.straight_line_distance(node, goal) * scale


def dijkstra(
    graph: CampusGraph,
    start: str,
    goal: str,
    priority: str = "NORMAL",
    battery_percentage: float = 100.0,
    accessible_only: bool = False,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> list[str] | None:
    """Find the least-cost route without using a heuristic."""

    if start not in graph.locations or goal not in graph.locations:
        return None

    open_set = [(0.0, start)]
    parent: dict[str, str | None] = {start: None}
    cost_so_far = {start: 0.0}

    while open_set:
        current_cost, current = heapq.heappop(open_set)

        if current_cost > cost_so_far[current]:
            continue

        if current == goal:
            return build_path(parent, goal)

        for road in graph.get_neighbors(current, accessible_only):
            neighbour = road.destination
            next_cost = current_cost + road_cost(
                road,
                priority,
                battery_percentage,
                traffic,
                weather
            )

            if (
                neighbour not in cost_so_far
                or next_cost < cost_so_far[neighbour]
            ):
                cost_so_far[neighbour] = next_cost
                parent[neighbour] = current
                heapq.heappush(
                    open_set,
                    (next_cost, neighbour)
                )

    return None


def build_path(
    parent: dict[str, str | None],
    goal: str
) -> list[str]:

    path = []
    current: str | None = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    return path
