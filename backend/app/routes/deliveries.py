import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query, Response

from ..agent import DeliveryTask
from ..delivery_service import DELIVERY_STATUSES
from ..map_service import resolve_location
from ..models import (
    DeliveryCreateRequest,
    DeliveryConfirmationRequest,
    DeliveryStatusUpdate,
    MultiDeliveryRequest,
    ReplanRequest,
    RoadBlockRequest,
)
from ..optimization import optimize_deliveries
from ..response_models import ApiDict, ApiListItem
from ..readiness import enrich_route_result
from ..routing import plan_route
from ..runtime import (
    delivery_service,
    get_graph,
    incident_cache,
    incident_cache_lock,
)
from ..settings import settings

logger = logging.getLogger("campusroute.deliveries")
router = APIRouter()


def _battery_state(percentage: float) -> dict[str, str | float]:
    if percentage <= 15:
        return {
            "level": "CRITICAL",
            "label": "Charge now",
            "message": "Battery is critically low; stop and recharge before another leg.",
            "percentage": round(percentage, 2),
        }
    if percentage <= 30:
        return {
            "level": "LOW",
            "label": "Charge soon",
            "message": "Battery is low; finish only a short safe leg, then recharge.",
            "percentage": round(percentage, 2),
        }
    return {
        "level": "HEALTHY",
        "label": "Sufficient",
        "message": "Battery reserve is sufficient for the current plan.",
        "percentage": round(percentage, 2),
    }


def _delivery_plan_breakdown(
    graph,
    start_location: str,
    tasks: list[DeliveryTask],
    stop_order: list[str],
    battery_percentage: float,
    traffic: str,
    weather: str,
) -> tuple[list[dict], list[dict]]:
    task_by_id = {task.task_id: task for task in tasks}
    current_location = start_location
    remaining_battery = battery_percentage
    segments: list[dict] = []
    summaries: dict[str, dict] = {}

    for index, stop_label in enumerate(stop_order, start=1):
        kind, task_id = stop_label.split(":", maxsplit=1)
        task = task_by_id[task_id]
        target = task.pickup_location if kind == "PICKUP" else task.destination
        before = remaining_battery
        leg = plan_route(
            graph=graph,
            start=current_location,
            destination=target,
            algorithm="AUTO",
            priority=task.priority,
            battery_percentage=remaining_battery,
            traffic=traffic,
            weather=weather,
        )
        if not leg["success"]:
            continue
        remaining_battery = max(0.0, remaining_battery - leg["battery_used"])
        segments.append(
            {
                "sequence": index,
                "task_id": task_id,
                "kind": kind,
                "location": target,
                "location_name": graph.locations[target].name,
                "path": leg["path"],
                "path_names": leg["path_names"],
                "distance_km": leg["distance_km"],
                "estimated_time_minutes": leg["estimated_time_minutes"],
                "battery_before": round(before, 2),
                "battery_used": leg["battery_used"],
                "battery_after": round(remaining_battery, 2),
                "battery_state": _battery_state(remaining_battery),
                "algorithm": leg["algorithm"],
            }
        )
        summary = summaries.setdefault(
            task_id,
            {
                "task_id": task_id,
                "item_type": task.item_type,
                "priority": task.priority,
                "pickup_location": task.pickup_location,
                "destination": task.destination,
                "battery_before": round(before, 2),
                "battery_used": 0.0,
                "distance_km": 0.0,
                "estimated_time_minutes": 0,
            },
        )
        summary["battery_used"] = round(summary["battery_used"] + leg["battery_used"], 2)
        summary["distance_km"] = round(summary["distance_km"] + leg["distance_km"], 3)
        summary["estimated_time_minutes"] += leg["estimated_time_minutes"]
        summary["battery_after"] = round(remaining_battery, 2)
        summary["battery_state"] = _battery_state(remaining_battery)
        current_location = target

    return segments, list(summaries.values())


def _priority(emergency: bool, priority: str) -> str:
    return "EMERGENCY" if emergency else priority.upper()


def _admin_check(x_admin_key: str | None) -> None:
    if settings.admin_key and x_admin_key != settings.admin_key:
        raise HTTPException(status_code=403, detail="Valid X-Admin-Key is required.")


@router.post("/api/deliveries", response_model=ApiDict)
def create_delivery(request: DeliveryCreateRequest) -> dict:
    graph = get_graph(request.campus_id)
    pickup = resolve_location(graph, request.pickup_location)
    destination = resolve_location(graph, request.destination)
    if pickup is None:
        raise HTTPException(status_code=404, detail="Pickup location not found.")
    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found.")
    priority = _priority(request.emergency, request.priority)
    route = plan_route(
        graph=graph,
        start=pickup.id,
        destination=destination.id,
        algorithm="AUTO",
        priority=priority,
        battery_percentage=request.battery_percentage,
        accessible_only=request.accessible_only,
        traffic=request.traffic,
        weather=request.weather,
    )
    route = enrich_route_result(route)
    if not route["success"]:
        raise HTTPException(status_code=422, detail=route.get("message", "No route available."))
    return delivery_service.create_delivery(
        campus_id=request.campus_id,
        pickup_location=pickup.id,
        destination=destination.id,
        item_type=request.item_type,
        priority=priority,
        battery_percentage=request.battery_percentage,
        route=route,
        accessible_only=request.accessible_only,
        receiver_name=request.receiver_name,
        delivery_note=request.delivery_note,
    )


@router.get("/api/deliveries", response_model=list[ApiListItem])
def get_deliveries(
    response: Response,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    records = delivery_service.get_all_deliveries()
    response.headers["X-Total-Count"] = str(len(records))
    return records[offset : offset + limit]


@router.post("/api/deliveries/optimize", response_model=ApiDict)
def optimize_delivery_batch(request: MultiDeliveryRequest) -> dict:
    graph = get_graph(request.campus_id)
    start = resolve_location(graph, request.starting_location)
    if start is None:
        raise HTTPException(status_code=404, detail="Starting location not found.")
    tasks = []
    for index, item in enumerate(request.tasks, start=1):
        pickup = resolve_location(graph, item.pickup_location)
        destination = resolve_location(graph, item.destination)
        if pickup is None or destination is None:
            raise HTTPException(status_code=404, detail=f"Invalid pickup or destination in delivery {index}.")
        tasks.append(
            DeliveryTask(
                task_id=f"TASK-{index:03d}",
                item_type=item.item_type.upper(),
                pickup_location=pickup.id,
                destination=destination.id,
                priority=item.priority,
            )
        )
    result = optimize_deliveries(
        graph=graph,
        starting_location=start.id,
        tasks=tasks,
        battery_percentage=request.battery_percentage,
        traffic=request.traffic,
        weather=request.weather,
    )
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])
    result["campus_id"] = request.campus_id
    segments, summaries = _delivery_plan_breakdown(
        graph=graph,
        start_location=start.id,
        tasks=tasks,
        stop_order=result["stop_order"],
        battery_percentage=request.battery_percentage,
        traffic=request.traffic,
        weather=request.weather,
    )
    result["delivery_segments"] = segments
    result["delivery_battery_summary"] = summaries
    result["initial_battery"] = _battery_state(request.battery_percentage)
    result["final_battery"] = _battery_state(result["battery_remaining"])
    result["task_destinations"] = [graph.locations[item].name for item in result["task_destinations"]]
    result["combined_route_names"] = [graph.locations[item].name for item in result["combined_route"]]
    return result


@router.get("/api/deliveries/{delivery_id}", response_model=ApiDict)
def get_delivery(delivery_id: str) -> dict:
    delivery = delivery_service.get_delivery(delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found.")
    return delivery


@router.post("/api/deliveries/{delivery_id}/replan", response_model=ApiDict)
def replan_delivery(delivery_id: str, request: ReplanRequest) -> dict:
    delivery = delivery_service.get_delivery(delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found.")
    graph = get_graph(delivery.get("campus_id", "demo"))
    current = resolve_location(graph, request.current_location)
    destination = resolve_location(graph, delivery["destination"])
    if current is None or destination is None:
        raise HTTPException(status_code=404, detail="Current location or destination not found.")
    accessible_only = (
        delivery.get("accessible_only", False)
        if request.accessible_only is None
        else request.accessible_only
    )
    route = plan_route(
        graph=graph,
        start=current.id,
        destination=destination.id,
        algorithm="AUTO",
        priority=delivery["priority"],
        battery_percentage=request.battery_percentage,
        accessible_only=accessible_only,
        traffic=request.traffic,
        weather=request.weather,
    )
    route = enrich_route_result(route)
    if not route["success"]:
        raise HTTPException(status_code=422, detail=route.get("message", "No alternate route available."))
    try:
        delivery_service.update_status(delivery_id, "REPLANNING")
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    updated = delivery_service.attach_route(delivery_id, route)
    delivery_service.update_status(delivery_id, "IN_TRANSIT")
    return updated or delivery


@router.patch("/api/deliveries/{delivery_id}/status", response_model=ApiDict)
def update_delivery_status(delivery_id: str, request: DeliveryStatusUpdate) -> dict:
    status = request.status.upper()
    if status not in DELIVERY_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid delivery status.")
    try:
        delivery = delivery_service.update_status(delivery_id, status)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found.")
    return delivery


@router.post("/api/deliveries/{delivery_id}/confirm", response_model=ApiDict)
def confirm_delivery(
    delivery_id: str,
    request: DeliveryConfirmationRequest,
) -> dict:
    try:
        delivery = delivery_service.confirm_delivery(
            delivery_id,
            request.confirmation_code,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found.")
    return delivery


@router.post("/api/roads/block", response_model=ApiDict)
def block_road(request: RoadBlockRequest, x_admin_key: str | None = Header(default=None)) -> dict:
    _admin_check(x_admin_key)
    graph = get_graph(request.campus_id)
    source = resolve_location(graph, request.source)
    destination = resolve_location(graph, request.destination)
    if source is None or destination is None:
        raise HTTPException(status_code=404, detail="Location not found.")
    graph.block_road(source.id, destination.id)
    incident = {
        "id": str(uuid4()),
        "source": source.id,
        "destination": destination.id,
        "reason": request.reason,
        "severity": request.severity,
        "reported_at": datetime.now(UTC).isoformat(),
        "status": "OPEN",
    }
    with incident_cache_lock:
        incident_cache.setdefault(request.campus_id.strip().lower(), []).append(incident)
    return {"message": "Road blocked successfully.", "incident": incident}


@router.post("/api/roads/unblock", response_model=ApiDict)
def unblock_road(request: RoadBlockRequest, x_admin_key: str | None = Header(default=None)) -> dict:
    _admin_check(x_admin_key)
    graph = get_graph(request.campus_id)
    source = resolve_location(graph, request.source)
    destination = resolve_location(graph, request.destination)
    if source is None or destination is None:
        raise HTTPException(status_code=404, detail="Location not found.")
    graph.unblock_road(source.id, destination.id)
    with incident_cache_lock:
        incidents = incident_cache.get(request.campus_id.strip().lower(), [])
        for incident in incidents:
            if {
                incident["source"], incident["destination"]
            } == {source.id, destination.id}:
                incident["status"] = "RESOLVED"
                incident["resolved_at"] = datetime.now(UTC).isoformat()
    return {"message": "Road unblocked successfully."}
