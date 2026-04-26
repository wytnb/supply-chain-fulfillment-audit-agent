from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

SNAPSHOT_TIME = datetime.fromisoformat("2026-04-26T10:30:00+08:00")
SOURCE_SYSTEM = "mock_settlement"
ROOT_DIR = Path(__file__).resolve().parents[3]
MOCK_DATA_DIR = ROOT_DIR / "mock-data"


class SettlementServiceError(Exception):
    code = "INTERNAL_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidArgumentError(SettlementServiceError):
    code = "INVALID_ARGUMENT"


class NotFoundError(SettlementServiceError):
    code = "NOT_FOUND"


class DataConflictError(SettlementServiceError):
    code = "DATA_CONFLICT"


class RuleNotApplicableError(SettlementServiceError):
    code = "RULE_NOT_APPLICABLE"


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
def _packages() -> list[dict[str, Any]]:
    return _load_json("packages.json")


@lru_cache(maxsize=None)
def _fee_rules() -> list[dict[str, Any]]:
    return _load_json("fee_rules.json")


@lru_cache(maxsize=None)
def _shipments() -> list[dict[str, Any]]:
    return _load_json("shipments.json")


@lru_cache(maxsize=None)
def _carriers() -> list[dict[str, Any]]:
    return _load_json("carriers.json")


@lru_cache(maxsize=None)
def _orders() -> list[dict[str, Any]]:
    return _load_json("orders.json")


@lru_cache(maxsize=None)
def _compensation_cases() -> list[dict[str, Any]]:
    return _load_json("compensation_cases.json")


@lru_cache(maxsize=None)
def _settlement_bills() -> list[dict[str, Any]]:
    return _load_json("settlement_bills.json")


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidArgumentError(f"{field_name} is required")
    return value.strip()


def _require_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidArgumentError(f"{field_name} must be a number")
    return float(value)


def _parse_time(raw: str | None) -> datetime | None:
    return datetime.fromisoformat(raw) if raw else None


def _shipment_by_waybill(waybill_no: str) -> dict[str, Any]:
    waybill_no = _require_text(waybill_no, "waybill_no")
    for shipment in _shipments():
        if shipment["waybill_no"] == waybill_no:
            return shipment
    raise NotFoundError(f"shipment not found for waybill_no={waybill_no}")


def _shipment_by_order(order_no: str) -> dict[str, Any]:
    order_no = _require_text(order_no, "order_no")
    matches = [shipment for shipment in _shipments() if shipment["order_no"] == order_no]
    if not matches:
        raise NotFoundError(f"shipment not found for order_no={order_no}")
    return sorted(matches, key=lambda item: item["ship_time"])[0]


def _order_by_order_no(order_no: str) -> dict[str, Any]:
    order_no = _require_text(order_no, "order_no")
    for order in _orders():
        if order["order_no"] == order_no:
            return order
    raise NotFoundError(f"order not found for order_no={order_no}")


def _package_by_waybill(waybill_no: str) -> dict[str, Any]:
    waybill_no = _require_text(waybill_no, "waybill_no")
    for package in _packages():
        if package["waybill_no"] == waybill_no:
            return package
    raise NotFoundError(f"package not found for waybill_no={waybill_no}")


def _fee_rule(carrier_code: str, service_level: str) -> dict[str, Any]:
    carrier_code = _require_text(carrier_code, "carrier_code")
    service_level = _require_text(service_level, "service_level")
    for rule in _fee_rules():
        if rule["carrier_code"] == carrier_code and rule["service_level"] == service_level:
            return rule
    raise NotFoundError(f"fee rule not found for carrier_code={carrier_code}, service_level={service_level}")


def _carrier_profile(carrier_code: str, service_level: str) -> dict[str, Any]:
    for profile in _carriers():
        if profile["carrier_code"] == carrier_code and profile["service_level"] == service_level:
            return profile
    raise NotFoundError(f"carrier profile not found for carrier_code={carrier_code}, service_level={service_level}")


def _bill_by_waybill(waybill_no: str) -> dict[str, Any]:
    for bill in _settlement_bills():
        if bill["waybill_no"] == waybill_no:
            return bill
    raise NotFoundError(f"settlement bill not found for waybill_no={waybill_no}")


def _resolve_order_and_waybill(order_no: str | None, waybill_no: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    if waybill_no:
        shipment = _shipment_by_waybill(waybill_no)
        order = _order_by_order_no(shipment["order_no"])
        return order, shipment
    if order_no:
        order = _order_by_order_no(order_no)
        shipment = _shipment_by_order(order_no)
        return order, shipment
    raise InvalidArgumentError("order_no or waybill_no is required")


def _value_added_service_amounts(package: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"service_code": service_code, "amount": 0.0} for service_code in package.get("value_added_services", [])]


def _calculate_chargeable_weight(package: dict[str, Any], rule: dict[str, Any]) -> dict[str, float]:
    actual_weight = float(package["actual_weight_kg"])
    volume_weight = round(
        (
            float(package["length_cm"])
            * float(package["width_cm"])
            * float(package["height_cm"])
        )
        / float(rule["volume_divisor"]),
        2,
    )
    expected_chargeable_weight = round(max(actual_weight, volume_weight), 2)
    recorded_chargeable_weight = round(float(package["chargeable_weight_kg"]), 2)
    if abs(recorded_chargeable_weight - expected_chargeable_weight) > 0.01:
        raise DataConflictError(
            "recorded chargeable_weight_kg does not match actual/volume calculation"
        )
    return {
        "actual_weight_kg": round(actual_weight, 2),
        "volume_weight_kg": volume_weight,
        "chargeable_weight_kg": recorded_chargeable_weight,
    }


def _calculate_base_freight(chargeable_weight_kg: float, rule: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    first_weight_kg = float(rule["first_weight_kg"])
    first_weight_fee = float(rule["first_weight_fee"])
    additional_weight_unit_kg = float(rule["additional_weight_unit_kg"])
    additional_weight_fee = float(rule["additional_weight_fee"])

    if chargeable_weight_kg <= first_weight_kg:
        additional_units = 0
        amount = first_weight_fee
    else:
        additional_units = math.ceil((chargeable_weight_kg - first_weight_kg) / additional_weight_unit_kg)
        amount = first_weight_fee + additional_units * additional_weight_fee

    return round(amount, 2), {
        "first_weight_kg": first_weight_kg,
        "first_weight_fee": round(first_weight_fee, 2),
        "additional_weight_unit_kg": additional_weight_unit_kg,
        "additional_weight_units": additional_units,
        "additional_weight_fee": round(additional_weight_fee, 2),
    }


def _build_freight_context(waybill_no: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    shipment = _shipment_by_waybill(waybill_no)
    package = _package_by_waybill(waybill_no)
    rule = _fee_rule(shipment["carrier_code"], shipment["service_level"])
    weight_calc = _calculate_chargeable_weight(package, rule)
    base_amount, base_meta = _calculate_base_freight(weight_calc["chargeable_weight_kg"], rule)
    remote_area_fee = float(rule["remote_area_fee"]) if package.get("is_remote_area") else 0.0
    value_added_services = _value_added_service_amounts(package)
    value_added_total = round(sum(item["amount"] for item in value_added_services), 2)
    total_amount = round(base_amount + remote_area_fee + value_added_total, 2)
    breakdown = {
        "base_freight_amount": round(base_amount, 2),
        "remote_area_fee": round(remote_area_fee, 2),
        "value_added_service_fee": value_added_total,
        "total_amount": total_amount,
    }
    context = {
        "weight_calculation": {**weight_calc, **base_meta},
        "value_added_services": value_added_services,
        "fee_breakdown": breakdown,
    }
    return shipment, package, rule, context


def settlement_calculate_freight(*, waybill_no: str) -> tuple[dict[str, Any], TraceInfo]:
    shipment, _, _, context = _build_freight_context(waybill_no)
    data = {
        "waybill_no": shipment["waybill_no"],
        "chargeable_weight_kg": context["weight_calculation"]["chargeable_weight_kg"],
        "system_calculated_amount": context["fee_breakdown"]["total_amount"],
        "fee_breakdown": context["fee_breakdown"],
    }
    return data, TraceInfo(record_id=shipment["waybill_no"])


def settlement_get_fee_breakdown(*, waybill_no: str) -> tuple[dict[str, Any], TraceInfo]:
    shipment, package, rule, context = _build_freight_context(waybill_no)
    data = {
        "waybill_no": shipment["waybill_no"],
        "carrier_code": shipment["carrier_code"],
        "service_level": shipment["service_level"],
        "weight_calculation": {
            **context["weight_calculation"],
            "package_dimensions_cm": {
                "length_cm": package["length_cm"],
                "width_cm": package["width_cm"],
                "height_cm": package["height_cm"],
            },
            "volume_divisor": rule["volume_divisor"],
        },
        "value_added_services": context["value_added_services"],
        "fee_breakdown": context["fee_breakdown"],
    }
    return data, TraceInfo(record_id=shipment["waybill_no"])


def settlement_calculate_timeout_penalty(*, waybill_no: str) -> tuple[dict[str, Any], TraceInfo]:
    shipment = _shipment_by_waybill(waybill_no)
    carrier = _carrier_profile(shipment["carrier_code"], shipment["service_level"])
    rule = _fee_rule(shipment["carrier_code"], shipment["service_level"])
    package = _package_by_waybill(waybill_no)

    ship_time = _parse_time(shipment["ship_time"])
    end_time = _parse_time(shipment["signed_time"]) or SNAPSHOT_TIME
    if ship_time is None:
        raise NotFoundError(f"ship_time missing for waybill_no={waybill_no}")

    allowed_hours = float(carrier["default_sla_hours"])
    if package.get("is_remote_area"):
        allowed_hours += float(carrier["remote_area_extra_hours"])

    elapsed_hours = round((end_time - ship_time).total_seconds() / 3600, 2)
    timeout_hours = round(max(elapsed_hours - allowed_hours, 0.0), 2)
    grace_hours = float(rule["timeout_grace_hours"])
    penalty_charge_hours = max(timeout_hours - grace_hours, 0.0)
    penalty_amount = min(
        round(penalty_charge_hours * float(rule["timeout_penalty_per_hour"]), 2),
        float(rule["timeout_penalty_cap"]),
    )

    data = {
        "waybill_no": shipment["waybill_no"],
        "is_timeout": timeout_hours > 0,
        "timeout_hours": timeout_hours,
        "penalty_amount": round(penalty_amount, 2),
        "grace_hours": grace_hours,
        "sla_hours": allowed_hours,
        "penalty_charge_hours": round(penalty_charge_hours, 2),
    }
    return data, TraceInfo(record_id=shipment["waybill_no"])


def settlement_calculate_compensation(
    *, exception_type: str, order_no: str | None = None, waybill_no: str | None = None
) -> tuple[dict[str, Any], TraceInfo]:
    exception_type = _require_text(exception_type, "exception_type")
    order, shipment = _resolve_order_and_waybill(order_no, waybill_no)
    carrier = _carrier_profile(shipment["carrier_code"], shipment["service_level"])

    if not carrier.get("support_compensation", False):
        raise RuleNotApplicableError("carrier does not support compensation")

    for case in _compensation_cases():
        if case["exception_type"] == exception_type and (
            case["waybill_no"] == shipment["waybill_no"] or case["order_no"] == order["order_no"]
        ):
            data = {
                "order_no": order["order_no"],
                "waybill_no": shipment["waybill_no"],
                "exception_type": exception_type,
                "is_compensable": True,
                "compensation_amount": case["compensation_amount"],
                "manual_confirm_required": case["manual_confirm_required"],
                "case_no": case["case_no"],
                "damage_level": case["damage_level"],
                "evidence_status": case["evidence_status"],
            }
            return data, TraceInfo(record_id=case["case_no"])

    raise RuleNotApplicableError(
        f"no compensation rule applies for order_no={order['order_no']}, waybill_no={shipment['waybill_no']}"
    )


def settlement_audit_carrier_bill(
    *, waybill_no: str, carrier_bill_amount: float
) -> tuple[dict[str, Any], TraceInfo]:
    carrier_bill_amount = _require_number(carrier_bill_amount, "carrier_bill_amount")
    shipment, _, _, context = _build_freight_context(waybill_no)
    bill = _bill_by_waybill(waybill_no)

    recorded_bill_amount = float(bill["carrier_bill_amount"])
    if abs(recorded_bill_amount - carrier_bill_amount) > 0.01:
        raise DataConflictError("input carrier_bill_amount does not match settlement_bills.json")
    if bill["carrier_code"] != shipment["carrier_code"]:
        raise DataConflictError("carrier_code mismatch between shipment and settlement bill")

    system_amount = float(context["fee_breakdown"]["total_amount"])
    difference_amount = round(carrier_bill_amount - system_amount, 2)
    difference_reasons: list[str] = []
    if difference_amount > 0:
        difference_reasons.append("carrier_bill_exceeds_system_recalculation")
    elif difference_amount < 0:
        difference_reasons.append("carrier_bill_lower_than_system_recalculation")
    if context["value_added_services"]:
        difference_reasons.append("value_added_services_present_but_no_structured_fee_rule")
    if not difference_reasons:
        difference_reasons.append("no_difference")

    data = {
        "waybill_no": shipment["waybill_no"],
        "bill_no": bill["bill_no"],
        "system_calculated_amount": round(system_amount, 2),
        "carrier_bill_amount": round(carrier_bill_amount, 2),
        "difference_amount": difference_amount,
        "difference_reasons": difference_reasons,
        "bill_status": bill["bill_status"],
    }
    return data, TraceInfo(record_id=bill["bill_no"])


__all__ = [
    "DataConflictError",
    "InvalidArgumentError",
    "NotFoundError",
    "RuleNotApplicableError",
    "SNAPSHOT_TIME",
    "SettlementServiceError",
    "TraceInfo",
    "settlement_audit_carrier_bill",
    "settlement_calculate_compensation",
    "settlement_calculate_freight",
    "settlement_calculate_timeout_penalty",
    "settlement_get_fee_breakdown",
]
