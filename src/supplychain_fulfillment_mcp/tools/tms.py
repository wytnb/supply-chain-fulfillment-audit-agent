from __future__ import annotations

from typing import Any, Callable

from supplychain_fulfillment_mcp.services import tms as tms_service


def _success(data: dict[str, Any], trace: tms_service.TraceInfo) -> dict[str, Any]:
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": data,
        "trace": trace.as_dict(),
    }


def _error(exc: Exception) -> dict[str, Any]:
    code = getattr(exc, "code", "INTERNAL_ERROR")
    return {
        "success": False,
        "code": code,
        "message": str(exc),
        "data": {},
        "trace": {
            "source_system": tms_service.SOURCE_SYSTEM,
            "record_id": None,
            "snapshot_time": tms_service.SNAPSHOT_TIME.isoformat(),
        },
    }


def _invoke(fn: Callable[..., tuple[dict[str, Any], tms_service.TraceInfo]], **kwargs: Any) -> dict[str, Any]:
    try:
        data, trace = fn(**kwargs)
        return _success(data, trace)
    except Exception as exc:
        return _error(exc)


def tms_get_waybill_by_order(*, order_no: str, repository: Any = None, **_: Any) -> dict[str, Any]:
    return _invoke(tms_service.tms_get_waybill_by_order, order_no=order_no)


def tms_get_shipment_detail(*, waybill_no: str, repository: Any = None, **_: Any) -> dict[str, Any]:
    return _invoke(tms_service.tms_get_shipment_detail, waybill_no=waybill_no)


def tms_get_tracking_events(*, waybill_no: str, repository: Any = None, **_: Any) -> dict[str, Any]:
    return _invoke(tms_service.tms_get_tracking_events, waybill_no=waybill_no)


def tms_get_delivery_status(
    *, waybill_no: str | None = None, order_no: str | None = None, repository: Any = None, **_: Any
) -> dict[str, Any]:
    return _invoke(tms_service.tms_get_delivery_status, waybill_no=waybill_no, order_no=order_no)


def tms_get_carrier_profile(
    *, carrier_code: str, service_level: str | None = None, repository: Any = None, **_: Any
) -> dict[str, Any]:
    return _invoke(tms_service.tms_get_carrier_profile, carrier_code=carrier_code, service_level=service_level)


def tms_check_tracking_stagnation(*, waybill_no: str, repository: Any = None, **_: Any) -> dict[str, Any]:
    return _invoke(tms_service.tms_check_tracking_stagnation, waybill_no=waybill_no)


TOOLS = {
    "tms_get_waybill_by_order": tms_get_waybill_by_order,
    "tms_get_shipment_detail": tms_get_shipment_detail,
    "tms_get_tracking_events": tms_get_tracking_events,
    "tms_get_delivery_status": tms_get_delivery_status,
    "tms_get_carrier_profile": tms_get_carrier_profile,
    "tms_check_tracking_stagnation": tms_check_tracking_stagnation,
}


__all__ = [*TOOLS.keys(), "TOOLS"]
