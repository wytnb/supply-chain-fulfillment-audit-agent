from __future__ import annotations

import pytest

from supplychain_fulfillment_mcp.state import reset_ticket_overlay_state_for_tests
from supplychain_fulfillment_mcp.server import create_server


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ticket_overlay_state_for_tests()


async def _call_tool(server, name: str, arguments: dict[str, object]) -> dict[str, object]:
    result = await server.call_tool(name, arguments)
    assert isinstance(result, tuple)
    return result[1]


@pytest.mark.parametrize(
    ("scenario_id", "order_no", "expected_ticket_no", "expected_exception_type"),
    [
        ("D01", "O-20260420-1001", "TK-20260426-5001", "order_not_shipped_timeout"),
        ("D02", "O-20260424-1002", "TK-20260426-5002", "inventory_shortage"),
        ("D03", "O-20260422-1006", "TK-20260426-5003", "tracking_stagnation"),
        ("D04", "O-20260424-1004", "TK-20260426-5004", "abnormal_signed"),
        ("D05", "O-20260423-1005", "TK-20260426-5005", "freight_bill_difference"),
    ],
)
@pytest.mark.asyncio
async def test_d01_to_d05_ticket_listing_matches_mock_data(
    scenario_id: str,
    order_no: str,
    expected_ticket_no: str,
    expected_exception_type: str,
) -> None:
    server = create_server()
    response = await _call_tool(server, "ticket_list_by_order", {"order_no": order_no})

    assert response["success"] is True
    tickets = response["data"]["tickets"]
    assert response["data"]["order_no"] == order_no
    assert any(ticket["ticket_no"] == expected_ticket_no for ticket in tickets), scenario_id
    assert any(ticket["exception_type"] == expected_exception_type for ticket in tickets), scenario_id


@pytest.mark.asyncio
async def test_ticket_round_trip_create_get_append_and_list() -> None:
    server = create_server()

    created = await _call_tool(
        server,
        "ticket_create_exception_ticket",
        {
            "order_no": "O-NEW-20260426-9001",
            "exception_type": "inventory_shortage",
            "responsible_department": "inventory_planning",
            "suggested_actions": ["check replenishment ETA", "evaluate cross-warehouse transfer"],
            "current_owner": "planner_01",
            "record_time": "2026-04-26T12:00:00+08:00",
        },
    )

    assert created["success"] is True
    ticket_no = created["data"]["ticket_no"]
    assert ticket_no == "TK-20260426-5006"
    assert created["data"]["ticket_status"] == "DRAFT"

    status = await _call_tool(server, "ticket_get_ticket_status", {"ticket_no": ticket_no})
    assert status["data"]["current_owner"] == "planner_01"
    assert status["data"]["process_records"][0]["action"] == "draft_created"

    appended = await _call_tool(
        server,
        "ticket_append_process_record",
        {
            "ticket_no": ticket_no,
            "record_time": "2026-04-26T12:05:00+08:00",
            "record_content": "replenishment_requested",
            "actor": "planner_01",
        },
    )
    assert appended["data"]["record_appended"] is True
    assert appended["data"]["process_records"][-1]["action"] == "replenishment_requested"

    listed = await _call_tool(server, "ticket_list_by_order", {"order_no": "O-NEW-20260426-9001"})
    assert [ticket["ticket_no"] for ticket in listed["data"]["tickets"]] == [ticket_no]


@pytest.mark.asyncio
async def test_tool_error_codes_and_scenarios() -> None:
    server = create_server()

    invalid_create = await _call_tool(
        server,
        "ticket_create_exception_ticket",
        {
            "order_no": "O-INVALID-1",
            "exception_type": "unknown_exception",
            "responsible_department": "warehouse",
            "suggested_actions": ["x"],
        },
    )
    assert invalid_create["code"] == "INVALID_ARGUMENT"

    invalid_get = await _call_tool(server, "ticket_get_ticket_status", {"ticket_no": ""})
    assert invalid_get["code"] == "INVALID_ARGUMENT"

    missing_get = await _call_tool(server, "ticket_get_ticket_status", {"ticket_no": "TK-20990101-9999"})
    assert missing_get["code"] == "NOT_FOUND"

    missing_append = await _call_tool(
        server,
        "ticket_append_process_record",
        {
            "ticket_no": "TK-20990101-9999",
            "record_time": "2026-04-26T12:05:00+08:00",
            "record_content": "followup",
        },
    )
    assert missing_append["code"] == "NOT_FOUND"

    missing_list = await _call_tool(server, "ticket_list_by_order", {"order_no": "O-NO-TICKET"})
    assert missing_list["code"] == "NOT_FOUND"

    reserved_ticket = await _call_tool(server, "ticket_close_ticket", {"ticket_no": "TK-20260426-5001"})
    assert reserved_ticket["code"] == "RESERVED_TOOL"

    reserved_oms = await _call_tool(server, "oms_get_fulfillment_summary", {"order_no": "O-20260420-1001"})
    assert reserved_oms["code"] == "RESERVED_TOOL"

    d01 = await _call_tool(server, "wms_check_fulfillment_blockers", {"order_no": "O-20260420-1001"})
    assert d01["success"] is True
    assert d01["data"]["has_exception"] is True
    assert d01["data"]["exception_type"] == "picking_timeout"

    d02 = await _call_tool(
        server,
        "wms_get_inventory_snapshot",
        {"sku_code": "SKU-1003", "warehouse_code": "WH-SH-01"},
    )
    assert d02["success"] is True
    assert d02["data"]["available_qty"] == 0

    d02_lock = await _call_tool(server, "wms_get_inventory_lock_detail", {"order_no": "O-20260424-1002"})
    assert d02_lock["success"] is True
    assert d02_lock["data"]["lock_status"] == "LOCK_FAILED"

    d03 = await _call_tool(server, "tms_check_tracking_stagnation", {"waybill_no": "WB-20260422-1006"})
    assert d03["success"] is True
    assert d03["data"]["is_stagnated"] is True

    d03_penalty = await _call_tool(
        server,
        "settlement_calculate_timeout_penalty",
        {"waybill_no": "WB-20260422-1006"},
    )
    assert d03_penalty["success"] is True
    assert d03_penalty["data"]["penalty_amount"] == 25

    d04 = await _call_tool(server, "tms_get_delivery_status", {"waybill_no": "WB-20260424-1004"})
    assert d04["success"] is True
    assert d04["data"]["delivery_status"] == "ABNORMAL_SIGNED"

    d04_comp = await _call_tool(
        server,
        "settlement_calculate_compensation",
        {
            "order_no": "O-20260424-1004",
            "exception_type": "abnormal_signed",
        },
    )
    assert d04_comp["success"] is True
    assert d04_comp["data"]["compensation_amount"] == 899

    d05 = await _call_tool(
        server,
        "settlement_audit_carrier_bill",
        {"waybill_no": "WB-20260423-1005", "carrier_bill_amount": 118},
    )
    assert d05["success"] is True
    assert d05["data"]["difference_amount"] == 12
