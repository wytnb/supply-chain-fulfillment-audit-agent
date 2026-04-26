"""Envelope helpers shared by all MCP tool implementations."""

from __future__ import annotations

from typing import Any

from .config import get_config
from .errors import InvalidArgumentError, ToolError


def build_trace(
    *,
    source_system: str,
    record_id: str | None = None,
    snapshot_time: str | None = None,
) -> dict[str, Any]:
    return {
        "source_system": source_system,
        "record_id": record_id,
        "snapshot_time": snapshot_time or get_config().snapshot_time,
    }


def success_response(
    data: dict[str, Any],
    *,
    source_system: str,
    record_id: str | None = None,
    snapshot_time: str | None = None,
    message: str = "success",
) -> dict[str, Any]:
    return {
        "success": True,
        "code": "OK",
        "message": message,
        "data": data,
        "trace": build_trace(
            source_system=source_system,
            record_id=record_id,
            snapshot_time=snapshot_time,
        ),
    }


def error_response(
    error: ToolError,
    *,
    source_system: str,
    record_id: str | None = None,
    snapshot_time: str | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "code": error.code,
        "message": error.message,
        "data": {},
        "trace": build_trace(
            source_system=source_system,
            record_id=record_id,
            snapshot_time=snapshot_time,
        ),
    }


def is_envelope(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    return {"success", "code", "message", "data", "trace"} <= payload.keys()


def require_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidArgumentError(f"`{field_name}` is required and must be a non-empty string")
    return value.strip()
