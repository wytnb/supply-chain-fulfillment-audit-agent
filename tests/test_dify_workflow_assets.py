from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DSL_PATH = ROOT / "dify" / "supply_chain_fulfillment_audit_workflow.yml"
README_PATH = ROOT / "dify" / "README.md"


def test_dify_assets_exist() -> None:
    assert DSL_PATH.exists()
    assert README_PATH.exists()


def test_dify_workflow_yaml_has_expected_top_level_structure() -> None:
    payload = yaml.safe_load(DSL_PATH.read_text(encoding="utf-8"))

    assert payload["kind"] == "app"
    assert payload["app"]["mode"] == "workflow"
    assert payload["workflow"]["graph"]["nodes"]
    assert payload["workflow"]["graph"]["edges"]


def test_dify_workflow_contains_required_node_types_and_placeholders() -> None:
    payload = yaml.safe_load(DSL_PATH.read_text(encoding="utf-8"))
    nodes = payload["workflow"]["graph"]["nodes"]

    node_types = {node["data"]["type"] for node in nodes}
    assert "start" in node_types
    assert "parameter-extractor" in node_types
    assert "if-else" in node_types
    assert "tool" in node_types
    assert "knowledge-retrieval" in node_types
    assert "iteration" in node_types
    assert "code" in node_types
    assert "end" in node_types

    knowledge_nodes = [node for node in nodes if node["data"]["type"] == "knowledge-retrieval"]
    assert len(knowledge_nodes) == 5

    tool_nodes = [node for node in nodes if node["data"]["type"] == "tool"]
    assert tool_nodes
    assert all(node["data"]["provider_id"] == "supplychain_fulfillment" for node in tool_nodes)
    assert all(node["data"]["provider_type"] == "mcp" for node in tool_nodes)


def test_dify_workflow_every_user_facing_node_has_five_part_description() -> None:
    payload = yaml.safe_load(DSL_PATH.read_text(encoding="utf-8"))
    nodes = payload["workflow"]["graph"]["nodes"]

    for node in nodes:
        data = node["data"]
        node_type = data["type"]
        if node_type == "iteration-start":
            continue

        desc = data.get("desc", "")
        assert "【作用】" in desc, data["title"]
        assert "【输入】" in desc, data["title"]
        assert "【处理】" in desc, data["title"]
        assert "【输出】" in desc, data["title"]
        assert "【异常分支】" in desc, data["title"]


def test_dify_readme_mentions_required_rebinding_steps() -> None:
    content = README_PATH.read_text(encoding="utf-8")

    assert "Tools -> MCP" in content
    assert "Knowledge" in content
    assert "Studio -> 导入后的 Workflow" in content
    assert "supplychain_fulfillment" in content
    assert "MCP_SERVER_URL" in content
    assert "KB_BINDINGS" in content
    assert "dataset_ids" in content
