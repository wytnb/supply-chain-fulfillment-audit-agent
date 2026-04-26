from __future__ import annotations

from supplychain_fulfillment_mcp.config import get_config
from supplychain_fulfillment_mcp.server import (
    build_runtime_config,
    parse_args,
    resolve_fastmcp_transport,
)


def test_parse_args_defaults_to_stdio() -> None:
    args = parse_args([])

    assert args.transport == "stdio"
    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.path == "/mcp"
    assert args.json_response is True
    assert args.stateless_http is True


def test_build_runtime_config_applies_http_overrides() -> None:
    args = parse_args(
        [
            "--transport",
            "http",
            "--host",
            "0.0.0.0",
            "--port",
            "8080",
            "--path",
            "custom-mcp",
            "--no-json-response",
            "--no-stateless-http",
        ]
    )

    config = build_runtime_config(args, base_config=get_config())

    assert config.default_transport == "http"
    assert config.host == "0.0.0.0"
    assert config.port == 8080
    assert config.streamable_http_path == "/custom-mcp"
    assert config.json_response is False
    assert config.stateless_http is False


def test_resolve_fastmcp_transport_maps_http_to_streamable_http() -> None:
    assert resolve_fastmcp_transport("stdio") == "stdio"
    assert resolve_fastmcp_transport("http") == "streamable-http"
