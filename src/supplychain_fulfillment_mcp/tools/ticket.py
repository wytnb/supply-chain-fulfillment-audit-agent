from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from ..state import get_ticket_overlay_state


VALID_EXCEPTION_TYPES = {
    "order_not_shipped_timeout",
    "inventory_shortage",
    "tracking_stagnation",
    "abnormal_signed",
    "freight_bill_difference",
    "freight_bill_audit",
}

VALID_RESPONSIBLE_DEPARTMENTS = {
    "warehouse",
    "inventory_planning",
    "logistics",
    "manual_review",
    "finance",
    "customer_service",
}

TICKET_TOOL_ERROR_CODES = {
    "ticket_create_exception_ticket": ("INVALID_ARGUMENT",),
    "ticket_get_ticket_status": ("INVALID_ARGUMENT", "NOT_FOUND"),
    "ticket_append_process_record": ("INVALID_ARGUMENT", "NOT_FOUND"),
    "ticket_list_by_order": ("INVALID_ARGUMENT", "NOT_FOUND"),
}

RESERVED_TICKET_TOOL_NAMES = ("ticket_close_ticket",)


class TicketToolError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


@dataclass(frozen=True, slots=True)
class TicketToolSpec:
    name: str
    handler: Callable[..., dict[str, Any]]
    error_codes: tuple[str, ...]
    reserved: bool = False


def _raise_invalid(message: str, **details: Any) -> None:
    raise TicketToolError("INVALID_ARGUMENT", message, details=details)


def _raise_not_found(message: str, **details: Any) -> None:
    raise TicketToolError("NOT_FOUND", message, details=details)


def _validate_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _raise_invalid(f"{field_name} must be a non-empty string", field=field_name)
    return value.strip()


def _validate_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        _raise_invalid(f"{field_name} must be a non-empty list", field=field_name)
    cleaned = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            _raise_invalid(f"{field_name} entries must be non-empty strings", field=field_name)
        cleaned.append(item.strip())
    return cleaned


def _normalize_record_time(record_time: str | None) -> str:
    if record_time is None:
        return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    try:
        return datetime.fromisoformat(record_time).isoformat()
    except ValueError as exc:
        raise TicketToolError(
            "INVALID_ARGUMENT",
            "record_time must be a valid ISO-8601 timestamp",
            details={"field": "record_time"},
        ) from exc


def ticket_create_exception_ticket(
    *,
    exception_type: str,
    responsible_department: str,
    suggested_actions: list[str],
    order_no: str | None = None,
    waybill_no: str | None = None,
    current_owner: str | None = None,
    create_as_draft: bool = True,
    actor: str = "A08",
    record_time: str | None = None,
) -> dict[str, Any]:
    exception_type = _validate_non_empty_str(exception_type, "exception_type")
    responsible_department = _validate_non_empty_str(
        responsible_department,
        "responsible_department",
    )
    suggested_actions = _validate_string_list(suggested_actions, "suggested_actions")
    if exception_type not in VALID_EXCEPTION_TYPES:
        _raise_invalid(
            "exception_type is not supported by the MVP ticket tools",
            field="exception_type",
            value=exception_type,
        )
    if responsible_department not in VALID_RESPONSIBLE_DEPARTMENTS:
        _raise_invalid(
            "responsible_department is not supported by the MVP ticket tools",
            field="responsible_department",
            value=responsible_department,
        )
    if order_no is not None:
        order_no = _validate_non_empty_str(order_no, "order_no")
    if waybill_no is not None:
        waybill_no = _validate_non_empty_str(waybill_no, "waybill_no")
    if order_no is None and waybill_no is None:
        _raise_invalid("order_no or waybill_no is required", fields=["order_no", "waybill_no"])
    if current_owner is not None:
        current_owner = _validate_non_empty_str(current_owner, "current_owner")
    actor = _validate_non_empty_str(actor, "actor")

    state = get_ticket_overlay_state()
    ticket_no = state.next_ticket_no()
    ticket_status = "DRAFT" if create_as_draft else "OPEN"
    ticket = {
        "ticket_no": ticket_no,
        "order_no": order_no,
        "waybill_no": waybill_no,
        "exception_type": exception_type,
        "responsible_department": responsible_department,
        "ticket_status": ticket_status,
        "current_owner": current_owner,
        "suggested_actions": suggested_actions,
        "process_records": [
            {
                "time": _normalize_record_time(record_time),
                "actor": actor,
                "action": "draft_created" if create_as_draft else "created",
            }
        ],
    }
    state.create_ticket(ticket)
    return {
        "ticket_no": ticket_no,
        "ticket_status": ticket_status,
        "create_as_draft": create_as_draft,
    }


def ticket_get_ticket_status(*, ticket_no: str) -> dict[str, Any]:
    ticket_no = _validate_non_empty_str(ticket_no, "ticket_no")
    ticket = get_ticket_overlay_state().get_ticket(ticket_no)
    if ticket is None:
        _raise_not_found("ticket was not found", ticket_no=ticket_no)
    return {
        "ticket_no": ticket["ticket_no"],
        "ticket_status": ticket["ticket_status"],
        "current_owner": ticket.get("current_owner"),
        "process_records": list(ticket.get("process_records") or []),
    }


def ticket_append_process_record(
    *,
    ticket_no: str,
    record_time: str,
    record_content: str,
    actor: str = "A08",
) -> dict[str, Any]:
    ticket_no = _validate_non_empty_str(ticket_no, "ticket_no")
    record_content = _validate_non_empty_str(record_content, "record_content")
    actor = _validate_non_empty_str(actor, "actor")
    record = {
        "time": _normalize_record_time(record_time),
        "actor": actor,
        "action": record_content,
    }
    updated = get_ticket_overlay_state().append_process_record(ticket_no, record)
    if updated is None:
        _raise_not_found("ticket was not found", ticket_no=ticket_no)
    return {
        "ticket_no": ticket_no,
        "record_appended": True,
        "ticket_status": updated["ticket_status"],
        "process_records": list(updated.get("process_records") or []),
    }


def ticket_list_by_order(*, order_no: str) -> dict[str, Any]:
    order_no = _validate_non_empty_str(order_no, "order_no")
    tickets = get_ticket_overlay_state().list_tickets_by_order(order_no)
    if not tickets:
        _raise_not_found("no tickets were found for this order", order_no=order_no)
    return {
        "order_no": order_no,
        "tickets": [
            {
                "ticket_no": ticket["ticket_no"],
                "ticket_status": ticket["ticket_status"],
                "exception_type": ticket["exception_type"],
                "responsible_department": ticket["responsible_department"],
                "waybill_no": ticket.get("waybill_no"),
            }
            for ticket in tickets
        ],
    }


def get_ticket_tool_specs() -> tuple[TicketToolSpec, ...]:
    return (
        TicketToolSpec(
            name="ticket_create_exception_ticket",
            handler=ticket_create_exception_ticket,
            error_codes=TICKET_TOOL_ERROR_CODES["ticket_create_exception_ticket"],
        ),
        TicketToolSpec(
            name="ticket_get_ticket_status",
            handler=ticket_get_ticket_status,
            error_codes=TICKET_TOOL_ERROR_CODES["ticket_get_ticket_status"],
        ),
        TicketToolSpec(
            name="ticket_append_process_record",
            handler=ticket_append_process_record,
            error_codes=TICKET_TOOL_ERROR_CODES["ticket_append_process_record"],
        ),
        TicketToolSpec(
            name="ticket_list_by_order",
            handler=ticket_list_by_order,
            error_codes=TICKET_TOOL_ERROR_CODES["ticket_list_by_order"],
        ),
        TicketToolSpec(
            name="ticket_close_ticket",
            handler=_reserved_ticket_close_ticket,
            error_codes=("RESERVED_TOOL",),
            reserved=True,
        ),
    )


def _reserved_ticket_close_ticket(**_: Any) -> dict[str, Any]:
    raise TicketToolError(
        "RESERVED_TOOL",
        "ticket_close_ticket is reserved and must not be registered in the MVP server",
    )


def register_ticket_tools(registry: Any) -> Any:
    registered: dict[str, Callable[..., dict[str, Any]]] = {}
    for spec in get_ticket_tool_specs():
        if spec.reserved:
            continue
        if isinstance(registry, dict):
            registry[spec.name] = spec.handler
        elif hasattr(registry, "register_tool"):
            registry.register_tool(spec.name, spec.handler)
        elif hasattr(registry, "add_tool"):
            registry.add_tool(spec.name, spec.handler)
        elif hasattr(registry, "tools") and isinstance(registry.tools, dict):
            registry.tools[spec.name] = spec.handler
        else:
            raise TypeError("registry must support dict, register_tool, add_tool, or .tools")
        registered[spec.name] = spec.handler
    return registry if not isinstance(registry, dict) else registered
