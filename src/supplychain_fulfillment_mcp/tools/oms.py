"""OMS mock MCP tools."""

from __future__ import annotations

from typing import Any

from ..errors import InvalidArgumentError, NotFoundError, ToolError
from ..repository import MockDataRepository, get_repository
from ..responses import error_response, require_non_empty_str, success_response


def _oms_success(data: dict[str, Any], record: dict[str, Any], repo: MockDataRepository) -> dict[str, Any]:
    return success_response(
        data,
        source_system=repo.get_source_system("orders"),
        record_id=repo.get_record_id("orders", record),
        snapshot_time=repo.get_snapshot_time("orders"),
    )


def _oms_error(error: ToolError, repo: MockDataRepository) -> dict[str, Any]:
    return error_response(
        error,
        source_system=repo.get_source_system("orders"),
        snapshot_time=repo.get_snapshot_time("orders"),
    )


def oms_get_order_detail(*, order_no: str, repository: MockDataRepository | None = None, **_: Any) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        order_no = require_non_empty_str(order_no, "order_no")
        order = repo.get_order(order_no)
        data = {
            "order_no": order["order_no"],
            "order_status": order["order_status"],
            "payment_status": order["payment_status"],
            "fulfillment_status": order["fulfillment_status"],
            "promise_ship_deadline": order["promise_ship_deadline"],
            "warehouse_code": order["warehouse_code"],
            "carrier_code": order["carrier_code"],
            "service_level": order["service_level"],
        }
        return _oms_success(data, order, repo)
    except ToolError as exc:
        return _oms_error(exc, repo)


def oms_get_order_status(*, order_no: str, repository: MockDataRepository | None = None, **_: Any) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        order_no = require_non_empty_str(order_no, "order_no")
        order = repo.get_order(order_no)
        timeline = [
            {"status": "ORDER_CREATED", "time": order["order_time"]},
            {"status": "ORDER_PAID", "time": order["paid_time"]},
            {"status": order["order_status"], "time": order["order_time"]},
            {"status": order["fulfillment_status"], "time": order["promise_ship_deadline"]},
        ]
        data = {
            "order_status": order["order_status"],
            "fulfillment_status": order["fulfillment_status"],
            "cancel_status": order["cancel_status"],
            "order_status_timeline": timeline,
        }
        return _oms_success(data, order, repo)
    except ToolError as exc:
        return _oms_error(exc, repo)


def oms_get_payment_status(*, order_no: str, repository: MockDataRepository | None = None, **_: Any) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        order_no = require_non_empty_str(order_no, "order_no")
        order = repo.get_order(order_no)
        data = {
            "payment_status": order["payment_status"],
            "paid_time": order["paid_time"],
        }
        return _oms_success(data, order, repo)
    except ToolError as exc:
        return _oms_error(exc, repo)


def oms_get_order_address(
    *, order_no: str, need_masking: bool = True, repository: MockDataRepository | None = None, **_: Any
) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        order_no = require_non_empty_str(order_no, "order_no")
        order = repo.get_order(order_no)
        if not need_masking:
            raise InvalidArgumentError("`need_masking` must be true because only masked order addresses are available")
        data = {
            "province": order["province"],
            "city": order["city"],
            "district": order["district"],
            "address_detail_masked": order["address_detail_masked"],
        }
        return _oms_success(data, order, repo)
    except ToolError as exc:
        return _oms_error(exc, repo)


def oms_get_order_items(*, order_no: str, repository: MockDataRepository | None = None, **_: Any) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        order_no = require_non_empty_str(order_no, "order_no")
        order = repo.get_order(order_no)
        items = repo.list_order_items(order_no)
        if not items:
            raise NotFoundError(f"order items for order `{order_no}` not found")
        data = {
            "order_no": order_no,
            "items": [
                {
                    "sku_code": item["sku_code"],
                    "sku_name": item["sku_name"],
                    "qty": item["qty"],
                    "unit_price": item["unit_price"],
                    "line_amount": item["line_amount"],
                }
                for item in items
            ],
        }
        return success_response(
            data,
            source_system=repo.get_source_system("order_items"),
            record_id=repo.get_record_id("order_items", items[0]),
            snapshot_time=repo.get_snapshot_time("order_items"),
        )
    except ToolError as exc:
        return error_response(
            exc,
            source_system=repo.get_source_system("order_items"),
            snapshot_time=repo.get_snapshot_time("order_items"),
        )
