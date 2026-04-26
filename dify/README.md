# Dify Workflow DSL 导入说明

本文档对应可导入文件：

- `dify/supply_chain_fulfillment_audit_workflow.yml`

该 DSL 是一份“统一总流程”模板，覆盖以下 5 个 MVP 场景：

- `late_shipment`
- `inventory_shortage`
- `tracking_stagnation`
- `abnormal_signed`
- `freight_bill_audit`

它默认依赖：

- 1 个 MCP Server：`supplychain_fulfillment`
- 5 个逻辑知识库绑定
- 1 个可用的参数提取模型

## 1. 导入前必须先准备什么

### 1.1 准备 MCP Server

在目标 Dify 工作区先进入：

```text
Tools -> MCP
```

新增或编辑 MCP Server，并确保下面 3 项正确：

- `Server URL`：替换成目标环境真实可访问的 HTTP MCP 地址
- `Name`：可按环境自定义，例如 `Supply Chain Fulfillment MCP`
- `Server ID`：**必须是** `supplychain_fulfillment`

不要改 DSL 里的 `MCP Server ID`。正确做法是去目标工作区创建同 ID 的 MCP Server。

推荐 URL 示例：

- 本机联调：`http://127.0.0.1:8000/mcp`
- 局域网联调：`http://YOUR_HOST:8000/mcp`
- 远端服务：`https://YOUR_DOMAIN/mcp`

如果目标 Dify 无法访问该 URL，Workflow 里的 MCP Tool 节点都会失效。

### 1.2 准备知识库

在目标 Dify 工作区先进入：

```text
Knowledge
```

确保以下 5 个逻辑知识库已经存在：

- `kb_fulfillment_exception_rules`
- `kb_warehouse_operation_sop`
- `kb_carrier_sla_rules`
- `kb_freight_settlement_rules`
- `kb_customer_service_templates`

如果目标工作区还没有这些知识库，需要先创建并导入知识文档，再导入 Workflow。

### 1.3 准备模型

本 DSL 的 `Intent & Parameter Extractor` 默认写入了一个可替换模型配置：

- provider: `openai`
- model: `gpt-4o-mini`

如果目标 Dify 工作区没有该模型，不会影响你导入 YAML 文件本身，但你导入后需要进入节点把模型切换成目标环境里真实可用的模型。

## 2. 导入 DSL

进入：

```text
Studio -> Import DSL
```

选择文件：

```text
dify/supply_chain_fulfillment_audit_workflow.yml
```

导入成功后，不要立刻运行，先按下面的步骤逐项替换和重绑。

## 3. 导入后必须替换或检查的占位符

### 3.1 MCP 相关占位符

这份 DSL 对 MCP 的设计是：

- `provider_id = supplychain_fulfillment`
- `provider_name = supplychain_fulfillment`
- `provider_type = mcp`

你导入后**不用**在 YAML 里改这些值。
你需要做的是确认目标工作区里已经存在：

- `Server ID = supplychain_fulfillment`

以及它指向真实可用的：

- `MCP_SERVER_URL`

`MCP_SERVER_URL` 是必须按目标环境替换的真实配置项。

### 3.2 知识库相关占位符

DSL 中 5 个 Knowledge Retrieval 节点使用了静态 `dataset_ids` 占位值。这些值只是模板占位，不应依赖跨工作区直接复用。

你需要在导入后手工重绑以下 5 个节点：

| Workflow 节点 | 逻辑知识库 |
|---|---|
| `D01 Rule Retrieval` | `kb_fulfillment_exception_rules` + `kb_warehouse_operation_sop` + `kb_customer_service_templates` |
| `D02 Rule Retrieval` | `kb_fulfillment_exception_rules` + `kb_customer_service_templates` |
| `D03 Rule Retrieval` | `kb_carrier_sla_rules` + `kb_fulfillment_exception_rules` + `kb_customer_service_templates` |
| `D04 Rule Retrieval` | `kb_fulfillment_exception_rules` + `kb_carrier_sla_rules` + `kb_freight_settlement_rules` + `kb_customer_service_templates` |
| `D05 Rule Retrieval` | `kb_freight_settlement_rules` + `kb_carrier_sla_rules` |

这也是本文档里 `KB_BINDINGS` 的实际含义：逻辑知识库名与目标工作区真实知识库绑定关系。

### 3.3 可选的检索依赖项

当前 DSL 的 Knowledge Retrieval 节点统一使用了：

- `retrieval_mode: multiple`
- `top_k: 5`
- `score_threshold: 0.2`
- `reranking_enable: false`

这些属于可固定的通用策略参数，通常不需要改。

但如果你要启用：

- rerank model
- 特定 provider
- 特定 metadata filtering

那么这些属于 `KB_OPTIONAL_RETRIEVAL_DEPENDENCIES`，需要按目标工作区的可用模型和 provider 自行重配。

## 4. 导入后要去哪些界面改

### 4.1 Tools -> MCP

进入：

```text
Tools -> MCP
```

逐项检查：

1. MCP Server 是否存在
2. `Server ID` 是否为 `supplychain_fulfillment`
3. `Server URL` 是否为真实可访问地址
4. 如有鉴权，是否已经授权或重新连接

### 4.2 Knowledge

进入：

```text
Knowledge
```

逐项检查：

1. 5 个逻辑知识库是否都存在
2. 知识库内是否已导入规则文档
3. 若准备启用 rerank，目标 provider/model 是否可用

### 4.3 Studio -> 导入后的 Workflow

进入导入后的 Workflow 画布后，至少逐项检查下面这些节点。

#### 先检查参数提取模型节点

节点：

- `Intent & Parameter Extractor`

需要检查：

1. 模型 provider 是否在目标环境可用
2. 模型 name 是否在目标环境可用
3. 若不可用，切换成当前工作区已有模型

#### 再逐个重绑 5 个 Knowledge Retrieval 节点

节点：

- `D01 Rule Retrieval`
- `D02 Rule Retrieval`
- `D03 Rule Retrieval`
- `D04 Rule Retrieval`
- `D05 Rule Retrieval`

每个节点都要手工打开并重新选择知识库，不要依赖 YAML 内的占位 `dataset_ids`。

#### 再逐个检查 MCP Tool 节点

目标是确认所有 MCP Tool 节点都已经被 Dify 正确识别到：

- `supplychain_fulfillment / oms_get_order_detail`
- `supplychain_fulfillment / oms_get_order_status`
- `supplychain_fulfillment / oms_get_payment_status`
- `supplychain_fulfillment / oms_get_order_items`
- `supplychain_fulfillment / oms_get_order_address`
- `supplychain_fulfillment / wms_get_inventory_snapshot`
- `supplychain_fulfillment / wms_get_inventory_lock_detail`
- `supplychain_fulfillment / wms_get_order_warehouse_progress`
- `supplychain_fulfillment / wms_get_outbound_record`
- `supplychain_fulfillment / wms_check_fulfillment_blockers`
- `supplychain_fulfillment / tms_get_waybill_by_order`
- `supplychain_fulfillment / tms_get_shipment_detail`
- `supplychain_fulfillment / tms_get_tracking_events`
- `supplychain_fulfillment / tms_get_delivery_status`
- `supplychain_fulfillment / tms_get_carrier_profile`
- `supplychain_fulfillment / tms_check_tracking_stagnation`
- `supplychain_fulfillment / settlement_calculate_timeout_penalty`
- `supplychain_fulfillment / settlement_calculate_compensation`
- `supplychain_fulfillment / settlement_calculate_freight`
- `supplychain_fulfillment / settlement_get_fee_breakdown`
- `supplychain_fulfillment / settlement_audit_carrier_bill`
- `supplychain_fulfillment / ticket_create_exception_ticket`

如果任一 Tool 节点显示未配置、找不到 provider、找不到 tool：

1. 回到 `Tools -> MCP`
2. 确认 `Server ID = supplychain_fulfillment`
3. 确认该 MCP Server 已经拉取到工具列表
4. 回到 Workflow 重新打开节点检查

## 5. 哪些内容可以固定，哪些必须替换

### 5.1 可以固定在 DSL 中的内容

以下内容可以直接保留在 DSL 里，不需要按环境修改：

- Workflow 图结构
- 节点命名
- 节点描述
- 业务分支逻辑
- Code 节点逻辑
- 输出字段结构
- MCP `Server ID = supplychain_fulfillment`
- MCP 工具名
- Knowledge Retrieval 的 `top_k`
- Knowledge Retrieval 的 `score_threshold`
- 是否启用 rerank 的默认策略

### 5.2 必须在目标环境替换或重绑的内容

以下内容必须在目标环境中替换或重绑：

- `MCP_SERVER_URL`
- MCP 授权状态
- 5 个 Knowledge Retrieval 节点对应的真实知识库绑定
- 如果启用了 rerank，相关 provider / model
- 如果参数提取节点默认模型不可用，需替换模型 provider / model

## 6. 为什么不要直接复用 dataset_ids

跨工作区迁移时，Knowledge Retrieval 节点里的 `dataset_ids` 本质上是工作区相关配置，不应被当作稳定可移植标识。

实践规则：

- 不要把模板里的 `dataset_ids` 当成真实知识库 ID
- 导入后一定手工重绑 5 个 Knowledge Retrieval 节点
- 如果目标工作区换了知识库、换了模型、换了 rerank 策略，也只在 Studio 里改，不改 Workflow 业务逻辑

## 7. 建议的导入后验证顺序

1. 先验证 `Tools -> MCP` 里的 `supplychain_fulfillment`
2. 再验证 `Knowledge` 中 5 个知识库
3. 再打开 Workflow，先替换参数提取模型
4. 再重绑 5 个 Knowledge Retrieval 节点
5. 再逐个检查 MCP Tool 节点
6. 最后按下面的样例跑通 5 个场景

## 8. 推荐测试输入

### D01 late_shipment

```text
query = 订单 O-20260420-1001 为什么还没发货
order_no = O-20260420-1001
```

### D02 inventory_shortage

```text
query = 订单 O-20260424-1002 缺货了吗 为什么发不了
order_no = O-20260424-1002
```

### D03 tracking_stagnation

```text
query = 运单 WB-20260422-1006 为什么物流不动了
waybill_no = WB-20260422-1006
```

### D04 abnormal_signed

```text
query = 订单 O-20260424-1004 客户反馈已签收但没收到货
order_no = O-20260424-1004
```

### D05 freight_bill_audit

```text
query = 帮我审核运单 WB-20260423-1005 的承运商账单
waybill_no = WB-20260423-1005
carrier_bill_amount = 118
```

## 9. 已知边界

- 这份模板是 `workflow`，不是 `chatflow`
- 它不会执行正式派单、正式结单、实际扣罚或赔付
- `ticket_create_exception_ticket` 只创建草稿
- 知识库节点在跨工作区迁移后必须手动重绑
- 若目标环境模型 provider 不可用，需要手工替换参数提取节点模型
