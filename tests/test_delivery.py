from backend.app.delivery_service import DeliveryService
from backend.app.storage import JsonStorage


def create_service(tmp_path):
    storage_file = tmp_path / "deliveries.json"
    storage = JsonStorage(storage_file)

    return DeliveryService(storage)


def test_create_delivery(tmp_path):
    service = create_service(tmp_path)

    delivery = service.create_delivery(
        pickup_location="main_gate",
        destination="medical_centre",
        item_type="MEDICINE",
        priority="EMERGENCY",
        battery_percentage=80,
        route={
            "success": True,
            "distance_km": 1.3
        }
    )

    assert delivery["status"] == "CREATED"
    assert delivery["item_type"] == "MEDICINE"
    assert delivery["priority"] == "EMERGENCY"


def test_get_delivery(tmp_path):
    service = create_service(tmp_path)

    created = service.create_delivery(
        pickup_location="main_gate",
        destination="medical_centre",
        item_type="DOCUMENT",
        priority="NORMAL",
        battery_percentage=90
    )

    delivery = service.get_delivery(
        created["id"]
    )

    assert delivery is not None
    assert delivery["id"] == created["id"]


def test_update_delivery_status(tmp_path):
    service = create_service(tmp_path)

    created = service.create_delivery(
        pickup_location="main_gate",
        destination="girls_hostel",
        item_type="FOOD",
        priority="NORMAL",
        battery_percentage=90
    )

    updated = service.update_status(
        created["id"],
        "IN_TRANSIT"
    )

    assert updated is not None
    assert updated["status"] == "IN_TRANSIT"


def test_complete_delivery(tmp_path):
    service = create_service(tmp_path)

    created = service.create_delivery(
        pickup_location="main_gate",
        destination="medical_centre",
        item_type="MEDICINE",
        priority="EMERGENCY",
        battery_percentage=90
    )

    updated = service.update_status(
        created["id"],
        "DELIVERED"
    )

    assert updated["status"] == "DELIVERED"


def test_invalid_status(tmp_path):
    service = create_service(tmp_path)

    created = service.create_delivery(
        pickup_location="main_gate",
        destination="medical_centre",
        item_type="DOCUMENT",
        priority="NORMAL",
        battery_percentage=90
    )

    try:
        service.update_status(
            created["id"],
            "UNKNOWN_STATUS"
        )
        assert False
    except ValueError:
        assert True