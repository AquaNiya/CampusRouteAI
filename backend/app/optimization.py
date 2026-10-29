from dataclasses import dataclass
from itertools import permutations

from .agent import DeliveryTask
from .graph import CampusGraph
from .routing import plan_route

PRIORITY_WEIGHTS = {
    "NORMAL": 1.0,
    "HIGH": 3.0,
    "EMERGENCY": 8.0
}


@dataclass(frozen=True)
class DeliveryStop:
    task_index: int
    task_id: str
    kind: str
    location: str
    priority: str


def _stops_for(tasks: list[DeliveryTask]) -> list[DeliveryStop]:
    stops = []
    for index, task in enumerate(tasks):
        stops.extend([
            DeliveryStop(
                index,
                task.task_id,
                "PICKUP",
                task.pickup_location,
                task.priority.upper()
            ),
            DeliveryStop(
                index,
                task.task_id,
                "DROP",
                task.destination,
                task.priority.upper()
            )
        ])
    return stops


def _valid_sequence(sequence: tuple[DeliveryStop, ...] | list[DeliveryStop]) -> bool:
    picked = set()
    dropped = set()
    for stop in sequence:
        if stop.kind == "PICKUP":
            if stop.task_index in picked:
                return False
            picked.add(stop.task_index)
        else:
            if stop.task_index not in picked or stop.task_index in dropped:
                return False
            dropped.add(stop.task_index)
    return True


def _priority_penalty(sequence: tuple[DeliveryStop, ...] | list[DeliveryStop]) -> float:
    return sum(
        index * PRIORITY_WEIGHTS.get(stop.priority, 1.0)
        for index, stop in enumerate(sequence)
    )


def _greedy_sequence(
    graph: CampusGraph,
    starting_location: str,
    stops: list[DeliveryStop]
) -> list[DeliveryStop]:
    remaining = list(stops)
    picked = set()
    current = starting_location
    sequence = []

    while remaining:
        available = [
            stop for stop in remaining
            if stop.kind == "PICKUP" or stop.task_index in picked
        ]
        chosen = min(
            available,
            key=lambda stop: (
                graph.straight_line_distance(current, stop.location)
                - 0.02 * PRIORITY_WEIGHTS.get(stop.priority, 1.0),
                stop.kind == "DROP"
            )
        )
        sequence.append(chosen)
        remaining.remove(chosen)
        current = chosen.location
        if chosen.kind == "PICKUP":
            picked.add(chosen.task_index)

    return sequence


def _evaluate_stop_sequence(
    graph: CampusGraph,
    starting_location: str,
    sequence: tuple[DeliveryStop, ...] | list[DeliveryStop],
    tasks: list[DeliveryTask],
    battery_percentage: float,
    traffic: str,
    weather: str
) -> dict:
    if not _valid_sequence(sequence):
        return {"success": False, "message": "Pickup must precede drop-off."}

    current_location = starting_location
    combined_route = [starting_location]
    total_distance = 0.0
    total_cost = 0.0
    battery_used = 0.0
    remaining_battery = battery_percentage
    estimated_time_minutes = 0

    for stop in sequence:
        task = tasks[stop.task_index]
        leg = plan_route(
            graph=graph,
            start=current_location,
            destination=stop.location,
            algorithm="AUTO",
            priority=task.priority,
            battery_percentage=remaining_battery,
            traffic=traffic,
            weather=weather
        )
        if not leg["success"]:
            return {
                "success": False,
                "message": (
                    f"No feasible route to {stop.kind.lower()} "
                    f"for {stop.task_id}: {leg['message']}"
                )
            }

        combined_route.extend(leg["path"][1:])
        total_distance += leg["distance_km"]
        total_cost += leg["total_cost"]
        battery_used += leg["battery_used"]
        remaining_battery -= leg["battery_used"]
        estimated_time_minutes += leg["estimated_time_minutes"]
        current_location = stop.location

    priority_penalty = _priority_penalty(sequence)
    return {
        "success": True,
        "combined_route": combined_route,
        "total_distance": total_distance,
        "total_cost": total_cost,
        "priority_penalty": priority_penalty,
        "objective": total_cost + priority_penalty,
        "battery_used": battery_used,
        "battery_remaining": remaining_battery,
        "estimated_time_minutes": estimated_time_minutes,
        "sequence": list(sequence)
    }


def _two_opt(
    graph: CampusGraph,
    starting_location: str,
    sequence: list[DeliveryStop],
    tasks: list[DeliveryTask],
    battery_percentage: float,
    traffic: str,
    weather: str
) -> tuple[list[DeliveryStop], dict]:
    best_sequence = sequence
    best_result = _evaluate_stop_sequence(
        graph,
        starting_location,
        best_sequence,
        tasks,
        battery_percentage,
        traffic,
        weather
    )
    improved = True

    while improved:
        improved = False
        for first in range(len(best_sequence) - 1):
            for last in range(first + 2, len(best_sequence) + 1):
                candidate = (
                    best_sequence[:first]
                    + list(reversed(best_sequence[first:last]))
                    + best_sequence[last:]
                )
                if not _valid_sequence(candidate):
                    continue
                result = _evaluate_stop_sequence(
                    graph,
                    starting_location,
                    candidate,
                    tasks,
                    battery_percentage,
                    traffic,
                    weather
                )
                if result["success"] and result["objective"] < best_result.get("objective", float("inf")):
                    best_sequence = candidate
                    best_result = result
                    improved = True
    return best_sequence, best_result


def optimize_deliveries(
    graph: CampusGraph,
    starting_location: str,
    tasks: list[DeliveryTask],
    battery_percentage: float,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> dict:
    if not tasks:
        return {"success": False, "message": "No delivery tasks provided."}

    stops = _stops_for(tasks)
    planning_method = "brute-force precedence search" if len(stops) <= 6 else "nearest-neighbour + 2-opt"
    candidate_sequences = (
        [sequence for sequence in permutations(stops) if _valid_sequence(sequence)]
        if len(stops) <= 6
        else [_greedy_sequence(graph, starting_location, stops)]
    )

    best_sequence = None
    best_result = None
    for sequence in candidate_sequences:
        result = _evaluate_stop_sequence(
            graph,
            starting_location,
            sequence,
            tasks,
            battery_percentage,
            traffic,
            weather
        )
        if result["success"] and (
            best_result is None
            or result["objective"] < best_result["objective"]
        ):
            best_sequence = list(sequence)
            best_result = result

    if best_sequence is None or best_result is None:
        return {
            "success": False,
            "message": "No feasible order found within the battery budget."
        }

    if len(stops) > 6:
        best_sequence, best_result = _two_opt(
            graph,
            starting_location,
            best_sequence,
            tasks,
            battery_percentage,
            traffic,
            weather
        )
        if not best_result["success"]:
            return {"success": False, "message": "No feasible order found."}

    task_order = []
    for stop in best_sequence:
        if stop.kind == "PICKUP" and stop.task_id not in task_order:
            task_order.append(stop.task_id)

    interleaved = any(
        stop.kind == "PICKUP"
        for stop in best_sequence[1:]
    ) and any(
        stop.kind == "DROP"
        for stop in best_sequence[:-1]
    )
    why_order = (
        "The order minimises route cost plus a weighted priority-delay penalty; "
        "pickup and drop-off stops were allowed to interleave."
        if interleaved
        else
        "The order minimises route cost plus a weighted priority-delay penalty "
        "while preserving pickup-before-drop precedence."
    )

    return {
        "success": True,
        "task_order": task_order,
        "task_destinations": [
            tasks[next(index for index, task in enumerate(tasks) if task.task_id == task_id)].destination
            for task_id in task_order
        ],
        "stop_order": [
            f"{stop.kind}:{stop.task_id}"
            for stop in best_sequence
        ],
        "combined_route": best_result["combined_route"],
        "total_distance": round(best_result["total_distance"], 3),
        "total_cost": round(best_result["total_cost"], 3),
        "priority_penalty": round(best_result["priority_penalty"], 3),
        "battery_used": round(best_result["battery_used"], 2),
        "battery_remaining": round(best_result["battery_remaining"], 2),
        "estimated_time_minutes": best_result["estimated_time_minutes"],
        "why_order": why_order,
        "planning_method": planning_method,
        "traffic": traffic.upper(),
        "weather": weather.upper()
    }


def evaluate_order(
    graph: CampusGraph,
    starting_location: str,
    task_order: tuple[DeliveryTask, ...],
    battery_percentage: float,
    traffic: str = "NORMAL",
    weather: str = "CLEAR"
) -> dict:
    """Compatibility wrapper for the old pickup-then-drop ordering API."""
    sequence = []
    for index, task in enumerate(task_order):
        sequence.extend([
            DeliveryStop(index, task.task_id, "PICKUP", task.pickup_location, task.priority.upper()),
            DeliveryStop(index, task.task_id, "DROP", task.destination, task.priority.upper())
        ])
    return _evaluate_stop_sequence(
        graph,
        starting_location,
        sequence,
        list(task_order),
        battery_percentage,
        traffic,
        weather
    )
