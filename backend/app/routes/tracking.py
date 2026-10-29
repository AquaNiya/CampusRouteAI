import time
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from ..map_service import (
    find_nearest_location,
    get_campus_boundary,
    get_campus_max_gps_distance,
    point_inside_boundary,
)
from ..models import LiveLocationRequest
from ..response_models import ApiDict
from ..runtime import (
    get_graph,
    live_location_cache,
    live_location_cache_lock,
    live_location_cache_times,
)
from ..settings import settings

router = APIRouter()


def _evict_expired(now: float) -> None:
    expired = [
        key
        for key, created_at in live_location_cache_times.items()
        if now - created_at > settings.live_location_ttl_seconds
    ]
    for key in expired:
        live_location_cache.pop(key, None)
        live_location_cache_times.pop(key, None)


@router.post("/api/live-location", response_model=ApiDict)
def receive_live_location(request: LiveLocationRequest) -> dict:
    graph = get_graph(request.campus_id)
    nearest = find_nearest_location(
        graph,
        request.latitude,
        request.longitude,
        get_campus_max_gps_distance(request.campus_id),
    )
    boundary = get_campus_boundary(request.campus_id)
    inside_campus = (
        point_inside_boundary(request.latitude, request.longitude, boundary)
        if boundary
        else nearest["within_campus"]
    )
    now = time.time()
    record = {
        "delivery_id": request.delivery_id,
        "campus_id": request.campus_id,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "accuracy_m": request.accuracy_m,
        "speed_mps": request.speed_mps,
        "heading_degrees": request.heading_degrees,
        "inside_campus": inside_campus,
        "nearest_location_id": nearest["id"],
        "nearest_location_name": nearest["name"],
        "distance_from_nearest_km": nearest["distance_from_user_km"],
        "received_at": datetime.now(UTC).isoformat(),
    }
    with live_location_cache_lock:
        _evict_expired(now)
        if request.delivery_id in live_location_cache:
            live_location_cache.pop(request.delivery_id)
        while len(live_location_cache) >= settings.live_location_cache_size:
            oldest_key, _ = live_location_cache.popitem(last=False)
            live_location_cache_times.pop(oldest_key, None)
        live_location_cache[request.delivery_id] = record
        live_location_cache_times[request.delivery_id] = now
    return {
        **record,
        "message": (
            "Live location received inside campus."
            if inside_campus
            else "Live location received outside the configured campus boundary."
        ),
    }


@router.get("/api/live-location/{tracking_key}", response_model=ApiDict)
def get_live_location(tracking_key: str) -> dict:
    with live_location_cache_lock:
        _evict_expired(time.time())
        record = live_location_cache.get(tracking_key)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="No live location has been received for this delivery.",
        )
    return record
