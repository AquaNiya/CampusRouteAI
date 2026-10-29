import logging
from collections import OrderedDict
from threading import RLock

from fastapi import HTTPException

from .delivery_service import DeliveryService
from .map_service import load_campus_graph
from .settings import settings
from .storage import JsonStorage

logger = logging.getLogger("campusroute")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

graph_cache = {"demo": load_campus_graph("demo")}
storage = JsonStorage(settings.data_dir / "deliveries.json")
delivery_service = DeliveryService(storage)
live_location_cache: OrderedDict[str, dict] = OrderedDict()
live_location_cache_times: dict[str, float] = {}
live_location_cache_lock = RLock()
incident_cache: dict[str, list[dict]] = {}
incident_cache_lock = RLock()


def get_graph(campus_id: str):
    normalized = campus_id.strip().lower() or "demo"
    if normalized not in graph_cache:
        try:
            graph_cache[normalized] = load_campus_graph(normalized)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
    return graph_cache[normalized]
