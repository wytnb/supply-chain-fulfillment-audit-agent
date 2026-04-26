from __future__ import annotations

import pytest

from supplychain_fulfillment_mcp.server import create_server, get_tool_specs
from supplychain_fulfillment_mcp.state import reset_ticket_overlay_state_for_tests


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ticket_overlay_state_for_tests()


@pytest.mark.asyncio
async def test_server_registers_all_mvp_and_reserved_tools() -> None:
    server = create_server()

    tools = await server.list_tools()
    names = {tool.name for tool in tools}

    assert len(tools) == 27
    assert names == {spec.name for spec in get_tool_specs()}
    assert "oms_get_fulfillment_summary" in names
    assert "ticket_close_ticket" in names


@pytest.mark.asyncio
async def test_every_tool_schema_includes_common_metadata_fields() -> None:
    server = create_server()

    for tool in await server.list_tools():
        properties = tool.inputSchema["properties"]
        assert "request_id" in properties
        assert "trace_id" in properties
        assert "operator_role" in properties
        assert "operator_id" in properties
        assert "need_masking" in properties

    order_detail = {
        tool.name: tool.inputSchema for tool in await server.list_tools()
    }["oms_get_order_detail"]
    assert "order_no" in order_detail["required"]


def test_http_defaults_are_exposed_on_server_settings() -> None:
    server = create_server()

    assert server.settings.host == "127.0.0.1"
    assert server.settings.port == 8000
    assert server.settings.streamable_http_path == "/mcp"
    assert server.settings.json_response is True
    assert server.settings.stateless_http is True
