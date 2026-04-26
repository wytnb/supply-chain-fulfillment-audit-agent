"""FastMCP server assembly for the fulfillment mock tools."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from dataclasses import replace
from functools import partial
import inspect
from typing import Any, Callable, Sequence

from mcp.server.fastmcp import FastMCP

from .config import MCPConfig, get_config
from .errors import ReservedToolError, ToolError, coerce_tool_error
from .repository import MockDataRepository
from .responses import error_response, is_envelope, success_response
from .tools.oms import (
    oms_get_order_address,
    oms_get_order_detail,
    oms_get_order_items,
    oms_get_order_status,
    oms_get_payment_status,
)
from .tools.settlement import (
    settlement_audit_carrier_bill,
    settlement_calculate_compensation,
    settlement_calculate_freight,
    settlement_calculate_timeout_penalty,
    settlement_get_fee_breakdown,
)
from .tools.ticket import (
    ticket_append_process_record,
    ticket_create_exception_ticket,
    ticket_get_ticket_status,
    ticket_list_by_order,
)
from .tools.tms import (
    tms_check_tracking_stagnation,
    tms_get_carrier_profile,
    tms_get_delivery_status,
    tms_get_shipment_detail,
    tms_get_tracking_events,
    tms_get_waybill_by_order,
)
from .tools.wms import (
    wms_check_fulfillment_blockers,
    wms_get_inventory_lock_detail,
    wms_get_inventory_snapshot,
    wms_get_order_warehouse_progress,
    wms_get_outbound_record,
)


@dataclass(frozen=True, slots=True)
class ParamSpec:
    name: str
    annotation: Any
    default: Any = inspect.Signature.empty


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    source_system: str
    handler: Callable[..., dict[str, Any]]
    params: tuple[ParamSpec, ...]
    record_id_fields: tuple[str, ...]
    inject_repository: bool = False
    reserved: bool = False


COMMON_PARAMS: tuple[ParamSpec, ...] = (
    ParamSpec("request_id", str | None, None),
    ParamSpec("trace_id", str | None, None),
    ParamSpec("operator_role", str | None, None),
    ParamSpec("operator_id", str | None, None),
    ParamSpec("need_masking", bool, True),
)


def _reserved_tool(*, message: str, **_: Any) -> dict[str, Any]:
    raise ReservedToolError(message)


TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        "oms_get_order_detail",
        "Query order facts from the OMS snapshot.",
        "mock_oms",
        oms_get_order_detail,
        (ParamSpec("order_no", str),),
        ("order_no",),
        inject_repository=True,
    ),
    ToolSpec(
        "oms_get_order_status",
        "Query order status timeline from the OMS snapshot.",
        "mock_oms",
        oms_get_order_status,
        (ParamSpec("order_no", str),),
        ("order_no",),
        inject_repository=True,
    ),
    ToolSpec(
        "oms_get_payment_status",
        "Query payment status from the OMS snapshot.",
        "mock_oms",
        oms_get_payment_status,
        (ParamSpec("order_no", str),),
        ("order_no",),
        inject_repository=True,
    ),
    ToolSpec(
        "oms_get_order_address",
        "Query masked shipping address from the OMS snapshot.",
        "mock_oms",
        oms_get_order_address,
        (ParamSpec("order_no", str),),
        ("order_no",),
        inject_repository=True,
    ),
    ToolSpec(
        "oms_get_order_items",
        "Query order line items from the OMS snapshot.",
        "mock_oms",
        oms_get_order_items,
        (ParamSpec("order_no", str),),
        ("order_no",),
        inject_repository=True,
    ),
    ToolSpec(
        "wms_get_inventory_snapshot",
        "Query WMS inventory snapshot by SKU and warehouse.",
        "mock_wms",
        wms_get_inventory_snapshot,
        (ParamSpec("sku_code", str), ParamSpec("warehouse_code", str)),
        ("sku_code",),
        inject_repository=True,
    ),
    ToolSpec(
        "wms_get_inventory_lock_detail",
        "Query WMS inventory lock records by order.",
        "mock_wms",
        wms_get_inventory_lock_detail,
        (ParamSpec("order_no", str),),
        ("order_no",),
        inject_repository=True,
    ),
    ToolSpec(
        "wms_get_order_warehouse_progress",
        "Query warehouse task progress for an order.",
        "mock_wms",
        wms_get_order_warehouse_progress,
        (ParamSpec("order_no", str),),
        ("order_no",),
        inject_repository=True,
    ),
    ToolSpec(
        "wms_get_outbound_record",
        "Query outbound record for an order.",
        "mock_wms",
        wms_get_outbound_record,
        (ParamSpec("order_no", str),),
        ("order_no",),
        inject_repository=True,
    ),
    ToolSpec(
        "wms_check_fulfillment_blockers",
        "Summarize fulfillment blockers inside the warehouse.",
        "mock_wms",
        wms_check_fulfillment_blockers,
        (ParamSpec("order_no", str),),
        ("order_no",),
        inject_repository=True,
    ),
    ToolSpec(
        "tms_get_waybill_by_order",
        "Query waybill information by order number.",
        "mock_tms",
        tms_get_waybill_by_order,
        (ParamSpec("order_no", str),),
        ("order_no", "waybill_no"),
    ),
    ToolSpec(
        "tms_get_shipment_detail",
        "Query shipment details by waybill.",
        "mock_tms",
        tms_get_shipment_detail,
        (ParamSpec("waybill_no", str),),
        ("waybill_no",),
    ),
    ToolSpec(
        "tms_get_tracking_events",
        "Query tracking events by waybill.",
        "mock_tms",
        tms_get_tracking_events,
        (ParamSpec("waybill_no", str),),
        ("waybill_no",),
    ),
    ToolSpec(
        "tms_get_delivery_status",
        "Query delivery and proof-of-delivery status by waybill.",
        "mock_tms",
        tms_get_delivery_status,
        (ParamSpec("waybill_no", str),),
        ("waybill_no",),
    ),
    ToolSpec(
        "tms_get_carrier_profile",
        "Query carrier SLA profile by carrier and service level.",
        "mock_tms",
        tms_get_carrier_profile,
        (ParamSpec("carrier_code", str), ParamSpec("service_level", str)),
        ("carrier_code",),
    ),
    ToolSpec(
        "tms_check_tracking_stagnation",
        "Judge whether tracking is stagnated against structured SLA.",
        "mock_tms",
        tms_check_tracking_stagnation,
        (ParamSpec("waybill_no", str),),
        ("waybill_no",),
    ),
    ToolSpec(
        "settlement_calculate_freight",
        "Recalculate baseline freight for a waybill.",
        "mock_settlement",
        settlement_calculate_freight,
        (ParamSpec("waybill_no", str),),
        ("waybill_no",),
    ),
    ToolSpec(
        "settlement_get_fee_breakdown",
        "Return detailed freight fee breakdown for a waybill.",
        "mock_settlement",
        settlement_get_fee_breakdown,
        (ParamSpec("waybill_no", str),),
        ("waybill_no",),
    ),
    ToolSpec(
        "settlement_calculate_timeout_penalty",
        "Calculate timeout penalty for a waybill.",
        "mock_settlement",
        settlement_calculate_timeout_penalty,
        (ParamSpec("waybill_no", str),),
        ("waybill_no",),
    ),
    ToolSpec(
        "settlement_calculate_compensation",
        "Calculate compensation suggestion for an exception.",
        "mock_settlement",
        settlement_calculate_compensation,
        (
            ParamSpec("exception_type", str),
            ParamSpec("order_no", str | None, None),
            ParamSpec("waybill_no", str | None, None),
        ),
        ("order_no", "waybill_no"),
    ),
    ToolSpec(
        "settlement_audit_carrier_bill",
        "Audit carrier bill amount against system recalculation.",
        "mock_settlement",
        settlement_audit_carrier_bill,
        (ParamSpec("waybill_no", str), ParamSpec("carrier_bill_amount", float)),
        ("waybill_no",),
    ),
    ToolSpec(
        "ticket_create_exception_ticket",
        "Create an exception ticket draft in overlay state.",
        "mock_ticket",
        ticket_create_exception_ticket,
        (
            ParamSpec("exception_type", str),
            ParamSpec("responsible_department", str),
            ParamSpec("suggested_actions", list[str]),
            ParamSpec("order_no", str | None, None),
            ParamSpec("waybill_no", str | None, None),
            ParamSpec("current_owner", str | None, None),
            ParamSpec("create_as_draft", bool, True),
            ParamSpec("actor", str, "A08"),
            ParamSpec("record_time", str | None, None),
        ),
        ("ticket_no", "order_no", "waybill_no"),
    ),
    ToolSpec(
        "ticket_get_ticket_status",
        "Query current ticket status and process records.",
        "mock_ticket",
        ticket_get_ticket_status,
        (ParamSpec("ticket_no", str),),
        ("ticket_no",),
    ),
    ToolSpec(
        "ticket_append_process_record",
        "Append a process record to a ticket in overlay state.",
        "mock_ticket",
        ticket_append_process_record,
        (
            ParamSpec("ticket_no", str),
            ParamSpec("record_time", str),
            ParamSpec("record_content", str),
            ParamSpec("actor", str, "A08"),
        ),
        ("ticket_no",),
    ),
    ToolSpec(
        "ticket_list_by_order",
        "List tickets associated with an order.",
        "mock_ticket",
        ticket_list_by_order,
        (ParamSpec("order_no", str),),
        ("order_no",),
    ),
    ToolSpec(
        "oms_get_fulfillment_summary",
        "Reserved OMS tool kept for contract completeness.",
        "mock_oms",
        partial(
            _reserved_tool,
            message="oms_get_fulfillment_summary is reserved and not available in the MVP server",
        ),
        (ParamSpec("order_no", str),),
        ("order_no",),
        reserved=True,
    ),
    ToolSpec(
        "ticket_close_ticket",
        "Reserved Ticket tool kept for contract completeness.",
        "mock_ticket",
        partial(
            _reserved_tool,
            message="ticket_close_ticket is reserved and not available in the MVP server",
        ),
        (ParamSpec("ticket_no", str),),
        ("ticket_no",),
        reserved=True,
    ),
)


def get_tool_specs() -> tuple[ToolSpec, ...]:
    return TOOL_SPECS


def _resolve_record_id(spec: ToolSpec, payload: dict[str, Any] | None, args: dict[str, Any]) -> str | None:
    sources = [payload or {}, args]
    for field in spec.record_id_fields:
        for source in sources:
            value = source.get(field)
            if value not in (None, ""):
                return str(value)
    return None


def _build_signature(spec: ToolSpec) -> inspect.Signature:
    parameters = [
        inspect.Parameter(
            param.name,
            inspect.Parameter.KEYWORD_ONLY,
            default=param.default,
            annotation=param.annotation,
        )
        for param in (*spec.params, *COMMON_PARAMS)
    ]
    return inspect.Signature(parameters=parameters, return_annotation=dict[str, object])


def _make_tool_callable(
    spec: ToolSpec,
    *,
    repository: MockDataRepository,
    config: MCPConfig,
) -> Callable[..., dict[str, object]]:
    business_param_names = {param.name for param in spec.params}

    def tool_callable(**kwargs: Any) -> dict[str, object]:
        business_kwargs = {name: kwargs.get(name) for name in business_param_names}
        if spec.inject_repository:
            business_kwargs["repository"] = repository
        try:
            payload = spec.handler(**business_kwargs)
            if is_envelope(payload):
                return payload
            record_id = _resolve_record_id(spec, payload, business_kwargs)
            return success_response(
                payload,
                source_system=spec.source_system,
                record_id=record_id,
                snapshot_time=config.snapshot_time,
            )
        except Exception as exc:
            error = coerce_tool_error(exc)
            record_id = _resolve_record_id(spec, None, business_kwargs)
            return error_response(
                error,
                source_system=spec.source_system,
                record_id=record_id,
                snapshot_time=config.snapshot_time,
            )

    tool_callable.__name__ = spec.name
    tool_callable.__qualname__ = spec.name
    tool_callable.__doc__ = spec.description
    tool_callable.__annotations__ = {
        param.name: param.annotation for param in (*spec.params, *COMMON_PARAMS)
    }
    tool_callable.__annotations__["return"] = dict[str, object]
    tool_callable.__signature__ = _build_signature(spec)
    return tool_callable


def create_server(
    *,
    config: MCPConfig | None = None,
    repository: MockDataRepository | None = None,
) -> FastMCP:
    resolved_config = config or get_config()
    resolved_repository = repository or MockDataRepository(resolved_config)
    server = FastMCP(
        name=resolved_config.server_name,
        host=resolved_config.host,
        port=resolved_config.port,
        streamable_http_path=resolved_config.streamable_http_path,
        json_response=resolved_config.json_response,
        stateless_http=resolved_config.stateless_http,
    )
    for spec in TOOL_SPECS:
        server.add_tool(
            _make_tool_callable(spec, repository=resolved_repository, config=resolved_config),
            name=spec.name,
            description=spec.description,
        )
    return server


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    base_config = get_config()
    parser = argparse.ArgumentParser(
        prog="supplychain-fulfillment-mcp",
        description="Run the supply chain fulfillment MCP mock server over stdio or HTTP.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default=base_config.default_transport,
        help="Transport to use for the MCP server.",
    )
    parser.add_argument(
        "--host",
        default=base_config.host,
        help="Host to bind when running over HTTP transport.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=base_config.port,
        help="Port to bind when running over HTTP transport.",
    )
    parser.add_argument(
        "--path",
        default=base_config.streamable_http_path,
        help="HTTP path for the streamable MCP endpoint.",
    )
    parser.add_argument(
        "--json-response",
        action=argparse.BooleanOptionalAction,
        default=base_config.json_response,
        help="Enable JSON HTTP responses for streamable-http transport.",
    )
    parser.add_argument(
        "--stateless-http",
        action=argparse.BooleanOptionalAction,
        default=base_config.stateless_http,
        help="Enable stateless HTTP mode for streamable-http transport.",
    )
    return parser.parse_args(argv)


def build_runtime_config(
    args: argparse.Namespace,
    *,
    base_config: MCPConfig | None = None,
) -> MCPConfig:
    current = base_config or get_config()
    path = args.path if args.path.startswith("/") else f"/{args.path}"
    return replace(
        current,
        default_transport=args.transport,
        host=args.host,
        port=args.port,
        streamable_http_path=path,
        json_response=args.json_response,
        stateless_http=args.stateless_http,
    )


def resolve_fastmcp_transport(transport: str) -> str:
    return "streamable-http" if transport == "http" else "stdio"


def run_server(config: MCPConfig) -> None:
    create_server(config=config).run(resolve_fastmcp_transport(config.default_transport))


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    run_server(build_runtime_config(args))


__all__ = [
    "ToolSpec",
    "build_runtime_config",
    "create_server",
    "get_tool_specs",
    "main",
    "parse_args",
    "resolve_fastmcp_transport",
    "run_server",
]


if __name__ == "__main__":
    main()
