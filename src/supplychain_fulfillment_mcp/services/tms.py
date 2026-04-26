from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

SNAPSHOT_TIME = datetime.fromisoformat("2026-04-26T10:30:00+08:00")
SOURCE_SYSTEM = "mock_tms"
ROOT_DIR = Path(__file__).resolve().parents[3]
MOCK_DATA_DIR = ROOT_DIR / "mock-data"


class TmsServiceError(Exception):
    code = "INTERNAL_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidArgumentError(TmsServiceError):
    code = "INVALID_ARGUMENT"


class NotFoundError(TmsServiceError):
    code = "NOT_FOUND"


@dataclass(frozen=True)
class TraceInfo:
    record_id: str
    source_system: str = SOURCE_SYSTEM
    snapshot_time: str = SNAPSHOT_TIME.isoformat()

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_system": self.source_system,
            "record_id": self.record_id,
            "snapshot_time": self.snapshot_time,
        }


def _load_json(filename: str) -> list[dict[str, Any]]:
    with (MOCK_DATA_DIR / filename).open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def _shipments() -> list[dict[str, Any]]:
    return _load_json("shipments.json")


@lru_cache(maxsize=None)
def _tracking_events() -> list[dict[str, Any]]:
    return _load_json("tracking_events.json")


@lru_cache(maxsize=None)
def _carriers() -> list[dict[str, Any]]:
    return _load_json("carriers.json")


@lru_cache(maxsize=None)
def _packages() -> list[dict[str, Any]]:
    return _load_json("packages.json")


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidArgumentError(f"{field_name} is required")
    return value.strip()


def _parse_time(raw: str | None) -> datetime | None:
    return datetime.fromisoformat(raw) if raw else None


def _get_shipment_by_waybill(waybill_no: str) -> dict[str, Any]:
    waybill_no = _require_text(waybill_no, "waybill_no")
    for shipment in _shipments():
        if shipment["waybill_no"] == waybill_no:
            return shipment
    raise NotFoundError(f"shipment not found for waybill_no={waybill_no}")


def _get_shipments_by_order(order_no: str) -> list[dict[str, Any]]:
    order_no = _require_text(order_no, "order_no")
    matches = [shipment for shipment in _shipments() if shipment["order_no"] == order_no]
    if not matches:
        raise NotFoundError(f"shipment not found for order_no={order_no}")
    return sorted(matches, key=lambda item: item["ship_time"])


def _get_tracking_by_waybill(waybill_no: str) -> list[dict[str, Any]]:
    waybill_no = _require_text(waybill_no, "waybill_no")
    matches = [event for event in _tracking_events() if event["waybill_no"] == waybill_no]
    if not matches:
        raise NotFoundError(f"tracking events not found for waybill_no={waybill_no}")
    return sorted(matches, key=lambda item: item["event_time"])


def _get_carrier_profile_record(carrier_code: str, service_level: str | None = None) -> dict[str, Any]:
    carrier_code = _require_text(carrier_code, "carrier_code")
    matches = [record for record in _carriers() if record["carrier_code"] == carrier_code]
    if service_level is not None:
        service_level = _require_text(service_level, "service_level")
        matches = [record for record in matches if record["service_level"] == service_level]
    if not matches:
        raise NotFoundError(
            f"carrier profile not found for carrier_code={carrier_code}"
            + (f", service_level={service_level}" if service_level else "")
        )
    if len(matches) > 1:
        raise InvalidArgumentError("service_level is required when multiple carrier profiles exist")
    return matches[0]


def _package_for_waybill(waybill_no: str) -> dict[str, Any] | None:
    for package in _packages():
        if package["waybill_no"] == waybill_no:
            return package
    return None


def _stagnation_threshold_hours(shipment: dict[str, Any], carrier_profile: dict[str, Any]) -> float:
    threshold = float(carrier_profile["default_sla_hours"])
    package = _package_for_waybill(shipment["waybill_no"])
    if package and package.get("is_remote_area"):
        threshold += float(carrier_profile["remote_area_extra_hours"])
    return threshold


def tms_get_waybill_by_order(*, order_no: str) -> tuple[dict[str, Any], TraceInfo]:
    shipments = _get_shipments_by_order(order_no)
    primary = shipments[0]
    data = {
        "order_no": order_no,
        "waybill_no": primary["waybill_no"],
        "ship_time": primary["ship_time"],
        "shipment_count": len(shipments),
        "waybills": [
            {
                "waybill_no": shipment["waybill_no"],
                "ship_time": shipment["ship_time"],
                "shipment_status": shipment["shipment_status"],
            }
            for shipment in shipments
        ],
    }
    return data, TraceInfo(record_id=primary["waybill_no"])


def tms_get_shipment_detail(*, waybill_no: str) -> tuple[dict[str, Any], TraceInfo]:
    shipment = _get_shipment_by_waybill(waybill_no)
    data = {
        "waybill_no": shipment["waybill_no"],
        "order_no": shipment["order_no"],
        "carrier_code": shipment["carrier_code"],
        "service_level": shipment["service_level"],
        "shipment_status": shipment["shipment_status"],
        "ship_time": shipment["ship_time"],
        "delivery_status": shipment["delivery_status"],
    }
    return data, TraceInfo(record_id=shipment["waybill_no"])


def tms_get_tracking_events(*, waybill_no: str) -> tuple[dict[str, Any], TraceInfo]:
    events = _get_tracking_by_waybill(waybill_no)
    data = {
        "waybill_no": waybill_no,
        "tracking_events": [
            {
                "event_time": event["event_time"],
                "event_type": event["event_type"],
                "event_desc": event["event_desc"],
                "event_city": event["event_city"],
            }
            for event in events
        ],
    }
    return data, TraceInfo(record_id=waybill_no)


def tms_get_delivery_status(
    *, waybill_no: str | None = None, order_no: str | None = None
) -> tuple[dict[str, Any], TraceInfo]:
    if waybill_no:
        shipment = _get_shipment_by_waybill(waybill_no)
    elif order_no:
        shipment = _get_shipments_by_order(order_no)[0]
    else:
        raise InvalidArgumentError("waybill_no or order_no is required")

    data = {
        "waybill_no": shipment["waybill_no"],
        "order_no": shipment["order_no"],
        "delivery_status": shipment["delivery_status"],
        "signed_time": shipment["signed_time"],
        "signed_by": shipment["signed_by"],
        "signed_proof_type": shipment["signed_proof_type"],
        "signed_proof_url": shipment["signed_proof_url"],
        "abnormal_reason": shipment["abnormal_reason"],
    }
    return data, TraceInfo(record_id=shipment["waybill_no"])


def tms_get_carrier_profile(*, carrier_code: str, service_level: str | None = None) -> tuple[dict[str, Any], TraceInfo]:
    profile = _get_carrier_profile_record(carrier_code, service_level)
    data = {
        "carrier_code": profile["carrier_code"],
        "service_level": profile["service_level"],
        "carrier_name": profile["carrier_name"],
        "default_sla_hours": profile["default_sla_hours"],
        "remote_area_extra_hours": profile["remote_area_extra_hours"],
        "support_compensation": profile["support_compensation"],
    }
    record_id = f"{profile['carrier_code']}:{profile['service_level']}"
    return data, TraceInfo(record_id=record_id)


def tms_check_tracking_stagnation(*, waybill_no: str) -> tuple[dict[str, Any], TraceInfo]:
    shipment = _get_shipment_by_waybill(waybill_no)
    events = _get_tracking_by_waybill(waybill_no)
    carrier_profile = _get_carrier_profile_record(shipment["carrier_code"], shipment["service_level"])

    last_event = events[-1]
    last_event_time = _parse_time(last_event["event_time"])
    if last_event_time is None:
        raise NotFoundError(f"last tracking event time missing for waybill_no={waybill_no}")

    hours_since_last_event = round((SNAPSHOT_TIME - last_event_time).total_seconds() / 3600, 2)
    threshold_hours = round(_stagnation_threshold_hours(shipment, carrier_profile), 2)
    data = {
        "waybill_no": shipment["waybill_no"],
        "shipment_status": shipment["shipment_status"],
        "is_stagnated": hours_since_last_event > threshold_hours,
        "hours_since_last_event": hours_since_last_event,
        "stagnation_threshold_hours": threshold_hours,
        "last_event": {
            "event_time": last_event["event_time"],
            "event_type": last_event["event_type"],
            "event_desc": last_event["event_desc"],
            "event_city": last_event["event_city"],
        },
    }
    return data, TraceInfo(record_id=shipment["waybill_no"])


__all__ = [
    "InvalidArgumentError",
    "NotFoundError",
    "SNAPSHOT_TIME",
    "TmsServiceError",
    "TraceInfo",
    "tms_check_tracking_stagnation",
    "tms_get_carrier_profile",
    "tms_get_delivery_status",
    "tms_get_shipment_detail",
    "tms_get_tracking_events",
    "tms_get_waybill_by_order",
]
