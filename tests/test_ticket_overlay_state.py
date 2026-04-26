from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from supplychain_fulfillment_mcp.state import TicketOverlayState


def test_overlay_keeps_baseline_immutable_and_visible() -> None:
    state = TicketOverlayState()

    baseline_ticket = state.get_ticket("TK-20260426-5003")
    assert baseline_ticket is not None
    assert baseline_ticket["ticket_status"] == "OPEN"

    created = state.create_ticket(
        {
            "ticket_no": "TK-20260426-5999",
            "order_no": "O-ROUNDTRIP-1",
            "waybill_no": None,
            "exception_type": "inventory_shortage",
            "responsible_department": "inventory_planning",
            "ticket_status": "DRAFT",
            "suggested_actions": ["check stock"],
            "process_records": [],
        }
    )

    assert created["ticket_no"] == "TK-20260426-5999"
    assert state.get_ticket("TK-20260426-5003")["ticket_status"] == "OPEN"
    assert any(ticket["ticket_no"] == "TK-20260426-5999" for ticket in state.snapshot())


def test_append_process_record_only_updates_overlay_copy() -> None:
    state = TicketOverlayState()

    updated = state.append_process_record(
        "TK-20260426-5004",
        {"time": "2026-04-26T11:00:00+08:00", "actor": "A08", "action": "evidence_requested"},
    )

    assert updated is not None
    assert updated["process_records"][-1]["action"] == "evidence_requested"

    fresh_state = TicketOverlayState()
    baseline = fresh_state.get_ticket("TK-20260426-5004")
    assert baseline is not None
    assert baseline["process_records"][-1]["action"] == "customer_claim_received"


def test_next_ticket_no_advances_from_latest_same_day_suffix() -> None:
    state = TicketOverlayState(now_fn=lambda: __import__("datetime").datetime(2026, 4, 26, 12, 0, 0))

    assert state.next_ticket_no() == "TK-20260426-5006"
    state.create_ticket(
        {
            "ticket_no": "TK-20260426-5006",
            "order_no": "O-ROUNDTRIP-2",
            "waybill_no": None,
            "exception_type": "order_not_shipped_timeout",
            "responsible_department": "warehouse",
            "ticket_status": "DRAFT",
            "suggested_actions": ["expedite"],
            "process_records": [],
        }
    )
    assert state.next_ticket_no() == "TK-20260426-5007"
