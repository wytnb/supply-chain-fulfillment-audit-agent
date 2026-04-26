from __future__ import annotations

from typing import Any, Callable

from supplychain_fulfillment_mcp.services import settlement as settlement_service


def _success(data: dict[str, Any], trace: settlement_service.TraceInfo) -> dict[str, Any]:
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
            "source_system": settlement_service.SOURCE_SYSTEM,
            "record_id": None,
            "snapshot_time": settlement_service.SNAPSHOT_TIME.isoformat(),
        },
    }


def _invoke(
    fn: Callable[..., tuple[dict[str, Any], settlement_service.TraceInfo]], **kwargs: Any
) -> dict[str, Any]:
    try:
        data, trace = fn(**kwargs)
        return _success(data, trace)
    except Exception as exc:
        return _error(exc)


def settlement_calculate_freight(*, waybill_no: str, repository: Any = None, **_: Any) -> dict[str, Any]:
    return _invoke(settlement_service.settlement_calculate_freight, waybill_no=waybill_no)


def settlement_get_fee_breakdown(*, waybill_no: str, repository: Any = None, **_: Any) -> dict[str, Any]:
    return _invoke(settlement_service.settlement_get_fee_breakdown, waybill_no=waybill_no)


def settlement_calculate_timeout_penalty(*, waybill_no: str, repository: Any = None, **_: Any) -> dict[str, Any]:
    return _invoke(settlement_service.settlement_calculate_timeout_penalty, waybill_no=waybill_no)


def settlement_calculate_compensation(
    *,
    exception_type: str,
    order_no: str | None = None,
    waybill_no: str | None = None,
    repository: Any = None,
    **_: Any,
) -> dict[str, Any]:
    return _invoke(
        settlement_service.settlement_calculate_compensation,
        exception_type=exception_type,
        order_no=order_no,
        waybill_no=waybill_no,
    )


def settlement_audit_carrier_bill(
    *, waybill_no: str, carrier_bill_amount: float, repository: Any = None, **_: Any
) -> dict[str, Any]:
    return _invoke(
        settlement_service.settlement_audit_carrier_bill,
        waybill_no=waybill_no,
        carrier_bill_amount=carrier_bill_amount,
    )


TOOLS = {
    "settlement_calculate_freight": settlement_calculate_freight,
    "settlement_get_fee_breakdown": settlement_get_fee_breakdown,
    "settlement_calculate_timeout_penalty": settlement_calculate_timeout_penalty,
    "settlement_calculate_compensation": settlement_calculate_compensation,
    "settlement_audit_carrier_bill": settlement_audit_carrier_bill,
}


__all__ = [*TOOLS.keys(), "TOOLS"]
