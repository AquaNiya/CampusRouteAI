from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["NORMAL", "HIGH", "EMERGENCY"]


class RouteRequest(BaseModel):
    campus_id: str = "demo"
    start: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    item_type: str = "OTHER"
    emergency: bool = False
    priority: Priority = "NORMAL"
    battery_percentage: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0
    )
    accessible_only: bool = False
    traffic: Literal["NORMAL", "HEAVY", "SEVERE"] = "NORMAL"
    weather: Literal["CLEAR", "RAIN", "STORM"] = "CLEAR"


class RoadBlockRequest(BaseModel):
    campus_id: str = "demo"
    source: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    reason: str = "Road incident reported by operator"
    severity: Literal["LOW", "HIGH", "CRITICAL"] = "HIGH"


class DeliveryCreateRequest(BaseModel):
    campus_id: str = "demo"
    pickup_location: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    item_type: str = "OTHER"
    emergency: bool = False
    priority: Priority = "NORMAL"
    battery_percentage: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0
    )
    accessible_only: bool = False
    traffic: Literal["NORMAL", "HEAVY", "SEVERE"] = "NORMAL"
    weather: Literal["CLEAR", "RAIN", "STORM"] = "CLEAR"
    receiver_name: str | None = None
    delivery_note: str | None = None


class MultiDeliveryTaskRequest(BaseModel):
    pickup_location: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    item_type: str = "OTHER"
    priority: Priority = "NORMAL"


class MultiDeliveryRequest(BaseModel):
    campus_id: str = "demo"
    starting_location: str = Field(min_length=1)
    tasks: list[MultiDeliveryTaskRequest] = Field(
        min_length=1,
        max_length=5
    )
    battery_percentage: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0
    )
    traffic: Literal["NORMAL", "HEAVY", "SEVERE"] = "NORMAL"
    weather: Literal["CLEAR", "RAIN", "STORM"] = "CLEAR"


class DeliveryStatusUpdate(BaseModel):
    status: str = Field(min_length=1)


class DeliveryConfirmationRequest(BaseModel):
    confirmation_code: str = Field(min_length=6, max_length=6)


class ReplanRequest(BaseModel):
    current_location: str = Field(min_length=1)
    battery_percentage: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0
    )
    accessible_only: bool | None = None
    traffic: Literal["NORMAL", "HEAVY", "SEVERE"] = "NORMAL"
    weather: Literal["CLEAR", "RAIN", "STORM"] = "CLEAR"


class LiveLocationRequest(BaseModel):
    campus_id: str = "demo"
    delivery_id: str = Field(min_length=1)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    accuracy_m: float | None = Field(default=None, ge=0.0)
    speed_mps: float | None = Field(default=None, ge=0.0)
    heading_degrees: float | None = Field(default=None, ge=0.0, le=360.0)
