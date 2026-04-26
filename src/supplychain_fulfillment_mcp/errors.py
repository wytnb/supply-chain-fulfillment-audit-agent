"""Shared error definitions for MCP tool responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ToolError(Exception):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class InvalidArgumentError(ToolError):
    def __init__(self, message: str) -> None:
        super().__init__("INVALID_ARGUMENT", message)


class NotFoundError(ToolError):
    def __init__(self, message: str) -> None:
        super().__init__("NOT_FOUND", message)


class DataConflictError(ToolError):
    def __init__(self, message: str) -> None:
        super().__init__("DATA_CONFLICT", message)


class RuleNotApplicableError(ToolError):
    def __init__(self, message: str) -> None:
        super().__init__("RULE_NOT_APPLICABLE", message)


class ReservedToolError(ToolError):
    def __init__(self, message: str) -> None:
        super().__init__("RESERVED_TOOL", message)


def coerce_tool_error(exc: Exception) -> ToolError:
    if isinstance(exc, ToolError):
        return exc

    code = getattr(exc, "code", "INVALID_ARGUMENT")
    message = getattr(exc, "message", str(exc))
    if code == "INVALID_ARGUMENT":
        return InvalidArgumentError(message)
    if code == "NOT_FOUND":
        return NotFoundError(message)
    if code == "DATA_CONFLICT":
        return DataConflictError(message)
    if code == "RULE_NOT_APPLICABLE":
        return RuleNotApplicableError(message)
    if code == "RESERVED_TOOL":
        return ReservedToolError(message)
    return ToolError(str(code), message)
