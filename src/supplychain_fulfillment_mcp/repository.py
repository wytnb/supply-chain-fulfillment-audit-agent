"""Read-only mock-data repository with in-memory indexes."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .config import MCPConfig, get_config
from .errors import NotFoundError


@dataclass(frozen=True, slots=True)
class TableMeta:
    name: str
    filename: str
    source_system: str
    record_id_field: str


TABLES: dict[str, TableMeta] = {
    "orders": TableMeta("orders", "orders.json", "mock_oms", "order_no"),
    "order_items": TableMeta("order_items", "order_items.json", "mock_oms", "order_no"),
    "inventory": TableMeta("inventory", "inventory.json", "mock_wms", "sku_code"),
    "inventory_locks": TableMeta("inventory_locks", "inventory_locks.json", "mock_wms", "order_no"),
    "warehouse_tasks": TableMeta("warehouse_tasks", "warehouse_tasks.json", "mock_wms", "task_no"),
    "outbound_records": TableMeta("outbound_records", "outbound_records.json", "mock_wms", "outbound_no"),
    "shipments": TableMeta("shipments", "shipments.json", "mock_tms", "waybill_no"),
    "tracking_events": TableMeta("tracking_events", "tracking_events.json", "mock_tms", "waybill_no"),
    "carriers": TableMeta("carriers", "carriers.json", "mock_tms", "carrier_code"),
    "packages": TableMeta("packages", "packages.json", "mock_settlement", "waybill_no"),
    "fee_rules": TableMeta("fee_rules", "fee_rules.json", "mock_settlement", "carrier_code"),
    "settlement_bills": TableMeta("settlement_bills", "settlement_bills.json", "mock_settlement", "bill_no"),
    "compensation_cases": TableMeta("compensation_cases", "compensation_cases.json", "mock_settlement", "case_no"),
    "exception_tickets": TableMeta("exception_tickets", "exception_tickets.json", "mock_ticket", "ticket_no"),
}


class MockDataRepository:
    def __init__(self, config: MCPConfig | None = None) -> None:
        self.config = config or get_config()
        self._tables: dict[str, list[dict[str, Any]]] = {}
        self._indexes: dict[tuple[str, str], dict[Any, list[dict[str, Any]]]] = {}

    def _table_path(self, table_name: str) -> Path:
        return self.config.mock_data_dir / TABLES[table_name].filename

    def _load_table(self, table_name: str) -> list[dict[str, Any]]:
        if table_name not in self._tables:
            path = self._table_path(table_name)
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, list):
                raise ValueError(f"{path} must contain a JSON list")
            self._tables[table_name] = data
        return self._tables[table_name]

    def _index(self, table_name: str, field_name: str) -> dict[Any, list[dict[str, Any]]]:
        key = (table_name, field_name)
        if key not in self._indexes:
            grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
            for row in self._load_table(table_name):
                grouped[row.get(field_name)].append(row)
            self._indexes[key] = dict(grouped)
        return self._indexes[key]

    def get_snapshot_time(self, table_name: str) -> str:
        self._load_table(table_name)
        return self.config.snapshot_time

    def get_source_system(self, table_name: str) -> str:
        return TABLES[table_name].source_system

    def get_record_id(self, table_name: str, record: dict[str, Any] | None) -> str | None:
        if record is None:
            return None
        return str(record.get(TABLES[table_name].record_id_field) or "")

    def get_order(self, order_no: str) -> dict[str, Any]:
        matches = self._index("orders", "order_no").get(order_no, [])
        if not matches:
            raise NotFoundError(f"order `{order_no}` not found")
        return matches[0]

    def list_order_items(self, order_no: str) -> list[dict[str, Any]]:
        return list(self._index("order_items", "order_no").get(order_no, []))

    def get_inventory_snapshot(self, sku_code: str, warehouse_code: str) -> dict[str, Any]:
        matches = self._index("inventory", "sku_code").get(sku_code, [])
        for record in matches:
            if record.get("warehouse_code") == warehouse_code:
                return record
        raise NotFoundError(
            f"inventory snapshot not found for sku `{sku_code}` in warehouse `{warehouse_code}`"
        )

    def list_inventory_locks(self, order_no: str) -> list[dict[str, Any]]:
        return list(self._index("inventory_locks", "order_no").get(order_no, []))

    def get_warehouse_task(self, order_no: str) -> dict[str, Any]:
        matches = self._index("warehouse_tasks", "order_no").get(order_no, [])
        if not matches:
            raise NotFoundError(f"warehouse task for order `{order_no}` not found")
        return matches[0]

    def get_outbound_record(self, order_no: str) -> dict[str, Any]:
        matches = self._index("outbound_records", "order_no").get(order_no, [])
        if not matches:
            raise NotFoundError(f"outbound record for order `{order_no}` not found")
        return matches[0]

    def get_shipment_by_waybill(self, waybill_no: str) -> dict[str, Any]:
        matches = self._index("shipments", "waybill_no").get(waybill_no, [])
        if not matches:
            raise NotFoundError(f"shipment for waybill `{waybill_no}` not found")
        return matches[0]

    def list_shipments_by_order(self, order_no: str) -> list[dict[str, Any]]:
        return sorted(
            self._index("shipments", "order_no").get(order_no, []),
            key=lambda item: item["ship_time"],
        )

    def list_tracking_events(self, waybill_no: str) -> list[dict[str, Any]]:
        return sorted(
            self._index("tracking_events", "waybill_no").get(waybill_no, []),
            key=lambda item: item["event_time"],
        )

    def get_carrier_profile(self, carrier_code: str, service_level: str) -> dict[str, Any]:
        for record in self._index("carriers", "carrier_code").get(carrier_code, []):
            if record.get("service_level") == service_level:
                return record
        raise NotFoundError(
            f"carrier profile not found for carrier `{carrier_code}` with service level `{service_level}`"
        )

    def get_package_by_waybill(self, waybill_no: str) -> dict[str, Any]:
        matches = self._index("packages", "waybill_no").get(waybill_no, [])
        if not matches:
            raise NotFoundError(f"package for waybill `{waybill_no}` not found")
        return matches[0]

    def get_fee_rule(self, carrier_code: str, service_level: str) -> dict[str, Any]:
        for record in self._index("fee_rules", "carrier_code").get(carrier_code, []):
            if record.get("service_level") == service_level:
                return record
        raise NotFoundError(
            f"fee rule not found for carrier `{carrier_code}` with service level `{service_level}`"
        )

    def get_settlement_bill_by_waybill(self, waybill_no: str) -> dict[str, Any]:
        matches = self._index("settlement_bills", "waybill_no").get(waybill_no, [])
        if not matches:
            raise NotFoundError(f"settlement bill for waybill `{waybill_no}` not found")
        return matches[0]

    def find_compensation_case(
        self,
        *,
        order_no: str | None = None,
        waybill_no: str | None = None,
        exception_type: str,
    ) -> dict[str, Any]:
        for record in self._load_table("compensation_cases"):
            if record.get("exception_type") != exception_type:
                continue
            if order_no and record.get("order_no") == order_no:
                return record
            if waybill_no and record.get("waybill_no") == waybill_no:
                return record
        raise NotFoundError("matching compensation case not found")


_repository: MockDataRepository | None = None


def get_repository() -> MockDataRepository:
    global _repository
    if _repository is None:
        _repository = MockDataRepository()
    return _repository
