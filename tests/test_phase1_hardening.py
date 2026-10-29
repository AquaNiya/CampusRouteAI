import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.api import app
from backend.app.delivery_service import DeliveryService
from backend.app.map_service import _campus_file
from backend.app.readiness import battery_state
from backend.app.storage import JsonStorage
from backend.app.validate_map import validate_map_file


def test_invalid_campus_id_is_rejected_before_path_lookup():
    with pytest.raises(ValueError, match="Invalid campus_id"):
        _campus_file("../secrets")


def test_atomic_storage_round_trip(tmp_path):
    storage = JsonStorage(tmp_path / "records.json")
    storage.save_records([{"id": "one"}])
    storage.add_record({"id": "two"})
    assert storage.load_records() == [{"id": "one"}, {"id": "two"}]
    assert not list(tmp_path.glob("*.tmp"))


def test_accessibility_is_stored_and_transition_is_validated(tmp_path):
    service = DeliveryService(JsonStorage(tmp_path / "records.json"))
    delivery = service.create_delivery(
        "main_gate",
        "medical_centre",
        "MEDICINE",
        "HIGH",
        80,
        accessible_only=True,
    )
    assert delivery["accessible_only"] is True
    service.update_status(delivery["id"], "ASSIGNED")
    with pytest.raises(ValueError, match="Invalid status transition"):
        service.update_status(delivery["id"], "CREATED")


def test_map_validator_loads_every_demo_map():
    for path in Path("backend/app/maps").glob("*.json"):
        result = validate_map_file(path)
        assert result["locations"] >= 20
        assert result["roads"] >= 35


def test_map_validator_reports_elevation_mismatch(tmp_path):
    data = {
        "campus": {"map_status": "DEMO", "source_note": "test"},
        "boundary": [[30, 78], [30, 79], [31, 79]],
        "locations": [
            {"id": "a", "name": "A", "latitude": 30, "longitude": 78, "type": "POINT", "elevation": 1},
            {"id": "b", "name": "B", "latitude": 30.001, "longitude": 78, "type": "POINT", "elevation": 5},
        ],
        "roads": [{"from": "a", "to": "b", "distance": 0.2, "elevation_gain": 1}],
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="elevation_gain"):
        validate_map_file(path)


def test_api_requires_delivery_id_for_live_location():
    response = TestClient(app).post(
        "/api/live-location",
        json={"campus_id": "demo", "latitude": 30.3165, "longitude": 78.0322},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_route_compare_exposes_battery_insufficient_path():
    response = TestClient(app).post(
        "/api/route/compare",
        json={
            "start": "main_gate",
            "destination": "medical_centre",
            "battery_percentage": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["battery_insufficient"] is True
    assert response.json()["comparison"]["A*"]["path"]
    assert response.json()["comparison"]["A*"]["battery_insufficient"] is True


def test_road_block_requires_configured_admin_key(monkeypatch):
    import backend.app.routes.deliveries as deliveries_module

    monkeypatch.setattr(deliveries_module.settings, "admin_key", "secret")
    response = TestClient(app).post(
        "/api/roads/block",
        json={"source": "main_gate", "destination": "south_parking"},
    )
    assert response.status_code == 403
    assert response.json()["error"] == "request_failed"


def test_live_location_cache_evicts_oldest_entry(monkeypatch):
    import backend.app.routes.tracking as tracking_module

    tracking_module.live_location_cache.clear()
    tracking_module.live_location_cache_times.clear()
    monkeypatch.setattr(tracking_module.settings, "live_location_cache_size", 2)
    client = TestClient(app)
    for delivery_id in ("one", "two", "three"):
        response = client.post(
            "/api/live-location",
            json={
                "delivery_id": delivery_id,
                "latitude": 30.3165,
                "longitude": 78.0322,
            },
        )
        assert response.status_code == 200
    assert client.get("/api/live-location/one").status_code == 404
    assert client.get("/api/live-location/three").status_code == 200


def test_api_rejects_backward_delivery_transition(tmp_path, monkeypatch):
    service = DeliveryService(JsonStorage(tmp_path / "records.json"))
    delivery = service.create_delivery(
        "main_gate",
        "medical_centre",
        "MEDICINE",
        "NORMAL",
        90,
        route={"success": True},
    )
    import backend.app.routes.deliveries as deliveries_module

    monkeypatch.setattr(deliveries_module, "delivery_service", service)
    service.update_status(delivery["id"], "ASSIGNED")
    response = TestClient(app).patch(
        f"/api/deliveries/{delivery['id']}/status",
        json={"status": "CREATED"},
    )
    assert response.status_code == 409


def test_deliveries_support_limit_and_offset(tmp_path, monkeypatch):
    service = DeliveryService(JsonStorage(tmp_path / "records.json"))
    for index in range(3):
        service.create_delivery("main_gate", "medical_centre", "BOOK", "NORMAL", 90)
    import backend.app.routes.deliveries as deliveries_module

    monkeypatch.setattr(deliveries_module, "delivery_service", service)
    response = TestClient(app).get("/api/deliveries?limit=1&offset=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.headers["x-total-count"] == "3"


def test_delivery_state_machine_supports_happy_path(tmp_path):
    service = DeliveryService(JsonStorage(tmp_path / "records.json"))
    delivery = service.create_delivery(
        "main_gate",
        "medical_centre",
        "MEDICINE",
        "EMERGENCY",
        90,
        route={"success": True},
    )
    for status in ("ASSIGNED", "IN_TRANSIT", "DELIVERED"):
        delivery = service.update_status(delivery["id"], status)
    assert delivery["status"] == "DELIVERED"


def test_demo_receiver_confirmation_records_proof(tmp_path):
    service = DeliveryService(JsonStorage(tmp_path / "records.json"))
    created = service.create_delivery(
        "main_gate",
        "medical_centre",
        "MEDICINE",
        "EMERGENCY",
        90,
        route={"success": True},
        receiver_name="Campus clinic",
    )
    assert len(created["demo_confirmation_code"]) == 6
    stored = service.get_delivery(created["id"])
    assert "demo_confirmation_code" not in stored
    assert stored["confirmation_code_hash"]
    with pytest.raises(ValueError, match="Invalid delivery confirmation"):
        service.confirm_delivery(created["id"], "000000")
    confirmed = service.confirm_delivery(
        created["id"],
        created["demo_confirmation_code"],
    )
    assert confirmed["status"] == "DELIVERED"
    assert confirmed["proof_of_delivery"]["method"] == "DEMO_OTP"


def test_battery_readiness_has_three_operational_states():
    assert battery_state(80)["level"] == "HEALTHY"
    assert battery_state(30)["level"] == "LOW"
    assert battery_state(15)["level"] == "CRITICAL"


def test_complex_demo_maps_are_exposed_by_api():
    client = TestClient(app)
    for campus_id in ("himalayan_demo", "plains_demo"):
        response = client.get(f"/api/map?campus_id={campus_id}")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload["locations"]) == 20
        assert len(payload["roads"]) >= 35
        assert len(payload["boundary"]) >= 3


def test_frontend_keeps_map_labels_and_delivery_completion_visuals():
    source = Path("frontend/app.js").read_text(encoding="utf-8")
    assert "permanent: true" in source
    assert "#16a34a" in source
    assert "innerHTML" not in source


def test_multi_delivery_response_contains_map_segments_and_battery_states():
    response = TestClient(app).post(
        "/api/deliveries/optimize",
        json={
            "campus_id": "demo",
            "starting_location": "main_gate",
            "battery_percentage": 80,
            "tasks": [
                {
                    "pickup_location": "main_gate",
                    "destination": "medical_centre",
                    "item_type": "MEDICINE",
                    "priority": "EMERGENCY",
                },
                {
                    "pickup_location": "academic_block",
                    "destination": "girls_hostel",
                    "item_type": "DOCUMENT",
                    "priority": "NORMAL",
                },
            ],
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["delivery_segments"]
    assert payload["delivery_battery_summary"][0]["battery_state"]["level"] in {
        "HEALTHY",
        "LOW",
        "CRITICAL",
    }
    assert payload["final_battery"]["percentage"] < 80
