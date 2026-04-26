# Supply Chain Fulfillment MCP Mock Server

面向供应链履约审计 Demo 的 MCP mock server，提供 5 个业务域、27 个工具名的本地模拟能力：

- 25 个 MVP 工具可调用
- 2 个 reserved 工具会返回 `RESERVED_TOOL`
- 所有工具统一返回 `success`、`code`、`message`、`data`、`trace`

设计文档入口见 [docs/README.md](./docs/README.md)。

## 如何开始

### 1. 环境前提

- Python `3.11+`
- 建议在项目根目录使用虚拟环境

初始化安装：

```bash
cd "/home/wyt/coding projects/supply-chain-fulfillment-audit-agent"
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

如果你的系统 Python 无法直接创建 `venv`，先安装对应系统包，或使用你现有的 Python 虚拟环境方案。

### 2. 本地以 `stdio` 启动

适用于 Claude Desktop、Cursor、MCP Inspector 这类本地 MCP 客户端。

```bash
cd "/home/wyt/coding projects/supply-chain-fulfillment-audit-agent"
source .venv/bin/activate
supplychain-fulfillment-mcp
```

等价写法：

```bash
.venv/bin/python -m supplychain_fulfillment_mcp.server
```

默认不传参数时，服务会使用 `stdio` transport。

### 3. 本地以 HTTP 启动

适用于 Dify 等只支持 HTTP transport 的 MCP 客户端。

```bash
cd "/home/wyt/coding projects/supply-chain-fulfillment-audit-agent"
source .venv/bin/activate
supplychain-fulfillment-mcp --transport http
```

等价写法：

```bash
.venv/bin/python -m supplychain_fulfillment_mcp.server --transport http
```

默认 HTTP MCP 地址：

```text
http://127.0.0.1:8000/mcp
```

常见自定义示例：

```bash
supplychain-fulfillment-mcp \
  --transport http \
  --host 0.0.0.0 \
  --port 8080 \
  --path /mcp
```

可用参数：

- `--transport stdio|http`
- `--host`
- `--port`
- `--path`
- `--json-response` / `--no-json-response`
- `--stateless-http` / `--no-stateless-http`

## 在 Dify 中添加 MCP

### 1. 先启动 HTTP 版本 MCP

Dify 当前只支持 **HTTP transport** 的 MCP server，因此不能直接接本项目默认的 `stdio` 启动方式。请先使用上一节的 HTTP 命令启动服务。

### 2. 在 Dify 中添加 Server

进入：

```text
Tools -> MCP -> Add MCP Server (HTTP)
```

按下面方式填写：

- `Server URL`：`http://127.0.0.1:8000/mcp`
- `Name`：例如 `Supply Chain Fulfillment MCP`
- `Server ID`：例如 `supplychain_fulfillment`

注意：

- `Server ID` 一旦开始被应用使用，就不要再修改，否则会影响已接入的 Agent / Workflow。
- 如果 Dify 和这个 MCP 服务不在同一台机器上，不要继续使用 `127.0.0.1`，必须改成 **Dify 实际可访问** 的地址。

官方说明可参考 Dify 文档：

- [Using MCP Tools](https://docs.dify.ai/en/use-dify/build/mcp)

### 3. 在 Dify 中使用这些工具

添加成功后，Dify 会自动发现这个 MCP server 暴露的工具。你可以在这些位置使用：

- `Agents`
- `Workflow`
- `Agent Node`

使用建议：

- 对固定参数使用 Dify 的 `Fixed` 值
- 对用户输入相关参数使用 `Auto`
- 保持开发、测试、生产环境的 `Server ID` 一致

## 开发与测试

运行测试：

```bash
cd "/home/wyt/coding projects/supply-chain-fulfillment-audit-agent"
source .venv/bin/activate
pytest -q
```

当前测试覆盖：

- 27 个工具注册与 schema
- `stdio` / HTTP 启动装配
- D01-D05 场景回归
- reserved 工具
- Ticket overlay round-trip
