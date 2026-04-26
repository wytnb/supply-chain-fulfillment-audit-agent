"""Runtime configuration for mock MCP tools."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True, slots=True)
class MCPConfig:
    """Configuration needed by the mock-data repository."""

    project_root: Path
    mock_data_dir: Path
    snapshot_time: str = "2026-04-26T10:30:00+08:00"
    default_timezone: str = "+08:00"
    enable_ephemeral_ticket_write: bool = True
    server_name: str = "supplychain-fulfillment-mcp-server"


def _resolve_project_root() -> Path:
    env_root = os.environ.get("SUPPLYCHAIN_FULFILLMENT_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def get_config() -> MCPConfig:
    project_root = _resolve_project_root()
    mock_data_dir = project_root / "mock-data"
    return MCPConfig(project_root=project_root, mock_data_dir=mock_data_dir)
