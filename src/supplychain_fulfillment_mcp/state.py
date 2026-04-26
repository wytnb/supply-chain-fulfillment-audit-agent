from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_ticket_data_path() -> Path:
    return _repo_root() / "mock-data" / "exception_tickets.json"


def _load_json_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list payload in {path}")
    return [copy.deepcopy(item) for item in payload]


@dataclass(slots=True)
class TicketOverlayState:
    ticket_data_path: Path = field(default_factory=_default_ticket_data_path)
    now_fn: Any = datetime.now
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)
    _baseline_tickets: list[dict[str, Any]] = field(default_factory=list, init=False, repr=False)
    _baseline_by_no: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)
    _overlay_by_no: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.reload_baseline()

    def reload_baseline(self) -> None:
        with self._lock:
            baseline = _load_json_records(self.ticket_data_path)
            self._baseline_tickets = baseline
            self._baseline_by_no = {
                str(ticket["ticket_no"]): copy.deepcopy(ticket) for ticket in baseline
            }

    def reset_overlay(self) -> None:
        with self._lock:
            self._overlay_by_no.clear()

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            merged = {
                ticket_no: copy.deepcopy(ticket)
                for ticket_no, ticket in self._baseline_by_no.items()
            }
            for ticket_no, ticket in self._overlay_by_no.items():
                merged[ticket_no] = copy.deepcopy(ticket)
            return sorted(merged.values(), key=lambda item: str(item["ticket_no"]))

    def get_ticket(self, ticket_no: str) -> dict[str, Any] | None:
        with self._lock:
            if ticket_no in self._overlay_by_no:
                return copy.deepcopy(self._overlay_by_no[ticket_no])
            ticket = self._baseline_by_no.get(ticket_no)
            return copy.deepcopy(ticket) if ticket is not None else None

    def list_tickets_by_order(self, order_no: str) -> list[dict[str, Any]]:
        return [
            ticket
            for ticket in self.snapshot()
            if str(ticket.get("order_no") or "") == order_no
        ]

    def create_ticket(self, ticket: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            ticket_no = str(ticket["ticket_no"])
            self._overlay_by_no[ticket_no] = copy.deepcopy(ticket)
            return copy.deepcopy(self._overlay_by_no[ticket_no])

    def append_process_record(
        self,
        ticket_no: str,
        record: dict[str, Any],
    ) -> dict[str, Any] | None:
        with self._lock:
            ticket = self.get_ticket(ticket_no)
            if ticket is None:
                return None
            records = list(ticket.get("process_records") or [])
            records.append(copy.deepcopy(record))
            ticket["process_records"] = records
            self._overlay_by_no[ticket_no] = ticket
            return copy.deepcopy(ticket)

    def next_ticket_no(self) -> str:
        with self._lock:
            current_date = self.now_fn().strftime("%Y%m%d")
            max_suffix = 5000
            for ticket in self.snapshot():
                ticket_no = str(ticket.get("ticket_no") or "")
                prefix = f"TK-{current_date}-"
                if not ticket_no.startswith(prefix):
                    continue
                suffix = ticket_no.rsplit("-", 1)[-1]
                if suffix.isdigit():
                    max_suffix = max(max_suffix, int(suffix))
            return f"TK-{current_date}-{max_suffix + 1:04d}"


_GLOBAL_TICKET_STATE = TicketOverlayState()


def get_ticket_overlay_state() -> TicketOverlayState:
    return _GLOBAL_TICKET_STATE


def reset_ticket_overlay_state_for_tests() -> TicketOverlayState:
    _GLOBAL_TICKET_STATE.reload_baseline()
    _GLOBAL_TICKET_STATE.reset_overlay()
    return _GLOBAL_TICKET_STATE
