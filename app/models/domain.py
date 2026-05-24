"""Domain entities (Pydantic models)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Vehicle(BaseModel):
    vin: str = Field(..., pattern=r"^[A-HJ-NPR-Z0-9]{11,17}$")
    make: str
    model: str
    year: int = Field(..., ge=1990, le=2100)
    fleet_id: str | None = None
    mileage_km: float | None = None


class Claim(BaseModel):
    claim_id: str
    vin: str | None = None
    component: str
    failure_mode: str
    description: str
    repair_cost_usd: float = Field(0.0, ge=0.0)
    status: Literal["open", "in_progress", "closed", "denied"] = "open"
    opened_at: datetime
    closed_at: datetime | None = None
    resolution: str | None = None
    technician_notes: str | None = None
    mileage_km: float | None = None


class TelemetryPoint(BaseModel):
    vin: str
    timestamp: datetime
    metric: str          # e.g. "battery_voltage", "engine_temp_c", "rpm"
    value: float
    diagnostic_code: str | None = None
    anomaly_flag: bool = False


class Document(BaseModel):
    document_id: str
    title: str
    source: str
    kind: Literal["service_manual", "tsb", "sop", "troubleshooting_guide", "engineering_doc"]
    content: str
    component_tags: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
