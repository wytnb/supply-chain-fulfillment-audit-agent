"""WMS mock MCP tools."""

from __future__ import annotations

from typing import Any

from ..errors import NotFoundError, ToolError
from ..repository import MockDataRepository, get_repository
from ..responses import error_response, require_non_empty_str, success_response


def wms_get_inventory_snapshot(
    *,
    sku_code: str,
    warehouse_code: str,
    repository: MockDataRepository | None = None,
    **_: Any,
) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        sku_code = require_non_empty_str(sku_code, "sku_code")
        warehouse_code = require_non_empty_str(warehouse_code, "warehouse_code")
        record = repo.get_inventory_snapshot(sku_code, warehouse_code)
        data = {
            "sku_code": record["sku_code"],
            "warehouse_code": record["warehouse_code"],
            "available_qty": record["available_qty"],
            "locked_qty": record["locked_qty"],
            "on_hand_qty": record["on_hand_qty"],
            "inventory_status": record["inventory_status"],
        }
        return success_response(
            data,
            source_system=repo.get_source_system("inventory"),
            record_id=repo.get_record_id("inventory", record),
            snapshot_time=repo.get_snapshot_time("inventory"),
        )
    except ToolError as exc:
        return error_response(
            exc,
            source_system=repo.get_source_system("inventory"),
            snapshot_time=repo.get_snapshot_time("inventory"),
        )


def wms_get_inventory_lock_detail(
    *,
    order_no: str,
    repository: MockDataRepository | None = None,
    **_: Any,
) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        order_no = require_non_empty_str(order_no, "order_no")
        repo.get_order(order_no)
        records = repo.list_inventory_locks(order_no)
        if not records:
            raise NotFoundError(f"inventory lock records for order `{order_no}` not found")
        total_required = sum(int(item["required_qty"]) for item in records)
        total_locked = sum(int(item["locked_qty"]) for item in records)
        total_shortage = sum(int(item["shortage_qty"]) for item in records)
        failed_reasons = [item["lock_failed_reason"] for item in records if item.get("lock_failed_reason")]
        overall_status = "LOCK_SUCCESS" if all(item["lock_status"] == "LOCK_SUCCESS" for item in records) else "LOCK_FAILED"
        data = {
            "order_no": order_no,
            "lock_status": overall_status,
            "required_qty": total_required,
            "locked_qty": total_locked,
            "shortage_qty": total_shortage,
            "lock_failed_reason": "; ".join(failed_reasons) if failed_reasons else None,
            "locks": records,
        }
        return success_response(
            data,
            source_system=repo.get_source_system("inventory_locks"),
            record_id=repo.get_record_id("inventory_locks", records[0]),
            snapshot_time=repo.get_snapshot_time("inventory_locks"),
        )
    except ToolError as exc:
        return error_response(
            exc,
            source_system=repo.get_source_system("inventory_locks"),
            snapshot_time=repo.get_snapshot_time("inventory_locks"),
        )


def wms_get_order_warehouse_progress(
    *,
    order_no: str,
    repository: MockDataRepository | None = None,
    **_: Any,
) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        order_no = require_non_empty_str(order_no, "order_no")
        repo.get_order(order_no)
        record = repo.get_warehouse_task(order_no)
        data = {
            "order_no": order_no,
            "warehouse_status": record["warehouse_status"],
            "current_node": record["current_node"],
            "current_owner": record["current_owner"],
            "last_update_time": record["last_update_time"],
        }
        return success_response(
            data,
            source_system=repo.get_source_system("warehouse_tasks"),
            record_id=repo.get_record_id("warehouse_tasks", record),
            snapshot_time=repo.get_snapshot_time("warehouse_tasks"),
        )
    except ToolError as exc:
        return error_response(
            exc,
            source_system=repo.get_source_system("warehouse_tasks"),
            snapshot_time=repo.get_snapshot_time("warehouse_tasks"),
        )


def wms_get_outbound_record(
    *,
    order_no: str,
    repository: MockDataRepository | None = None,
    **_: Any,
) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        order_no = require_non_empty_str(order_no, "order_no")
        repo.get_order(order_no)
        record = repo.get_outbound_record(order_no)
        data = {
            "order_no": order_no,
            "outbound_status": record["outbound_status"],
            "outbound_no": record["outbound_no"],
            "outbound_time": record["outbound_time"],
        }
        return success_response(
            data,
            source_system=repo.get_source_system("outbound_records"),
            record_id=repo.get_record_id("outbound_records", record),
            snapshot_time=repo.get_snapshot_time("outbound_records"),
        )
    except ToolError as exc:
        return error_response(
            exc,
            source_system=repo.get_source_system("outbound_records"),
            snapshot_time=repo.get_snapshot_time("outbound_records"),
        )


def wms_check_fulfillment_blockers(
    *,
    order_no: str,
    repository: MockDataRepository | None = None,
    **_: Any,
) -> dict[str, Any]:
    repo = repository or get_repository()
    try:
        order_no = require_non_empty_str(order_no, "order_no")
        repo.get_order(order_no)
        task = repo.get_warehouse_task(order_no)
        outbound = repo.get_outbound_record(order_no)

        exception_type = task.get("exception_type")
        exception_reason = task.get("exception_reason")
        if not exception_type and outbound.get("outbound_status") == "BLOCKED":
            exception_type = "outbound_blocked"
            exception_reason = "outbound record is blocked without a warehouse exception type"

        data = {
            "order_no": order_no,
            "has_exception": bool(exception_type),
            "exception_type": exception_type,
            "exception_reason": exception_reason,
            "warehouse_status": task["warehouse_status"],
            "outbound_status": outbound["outbound_status"],
        }
        return success_response(
            data,
            source_system=repo.get_source_system("warehouse_tasks"),
            record_id=repo.get_record_id("warehouse_tasks", task),
            snapshot_time=max(
                repo.get_snapshot_time("warehouse_tasks"),
                repo.get_snapshot_time("outbound_records"),
            ),
        )
    except ToolError as exc:
        return error_response(
            exc,
            source_system=repo.get_source_system("warehouse_tasks"),
            snapshot_time=repo.get_snapshot_time("warehouse_tasks"),
        )
