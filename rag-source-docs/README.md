# Dify RAG Source Docs

本目录用于存放可直接导入 Dify Knowledge Base 的 Markdown 源文档。

## 目录映射

- `fulfillment-exception/` -> `kb_fulfillment_exception_rules`
- `warehouse-sop/` -> `kb_warehouse_operation_sop`
- `carrier-sla/` -> `kb_carrier_sla_rules`
- `freight-settlement/` -> `kb_freight_settlement_rules`
- `customer-service/` -> `kb_customer_service_templates`

## 导入建议

- 规则型知识库：优先使用 `General`
- 较长的 SOP / SLA 文档：可使用 `Parent-child / Paragraph`
- 不建议直接把 `docs/*.md` 设计文档整篇导入 Dify；本目录中的文档已经按单主题拆分
- 每个 Markdown 文件在 Dify 中对应一个 Document
- 单文件建议保持单一主题，避免把多个场景混在同一篇文档中

## 推荐 Metadata

- `kb_type`
- `rule_id`
- `scenario_code`
- `exception_type`
- `role`
- `version`
- `source`
- `effective_date`

Metadata 字段名建议只使用小写字母、数字和下划线。

## 文档结构约定

规则型文档统一包含：

- 顶部固定字段：规则编号、规则名称、知识库、适用场景、适用角色、规则版本、是否模拟规则、关联测试编号
- 正文固定段落：`规则摘要`、`触发条件`、`需要查询的数据`、`判断逻辑`、`责任归因`、`处理建议`、`升级条件`
- 按需补充：`客服表达建议`、`工单字段建议`

SOP 文档统一包含：

- `流程目标`
- `适用前提`
- `关键节点`
- `异常分支`
- `升级动作`
- `交接信息`

客服模板文档统一包含：

- 顶部固定字段：模板编号、模板名称、知识库、适用场景、适用角色、版本、是否模拟模板、关联测试编号
- `适用场景`
- `可说内容`
- `禁用表达`
- `回复模板`
- `需补充证据`
- `人工确认边界`

## 内容边界

本目录中的 RAG 文档只负责：

- 解释规则
- 说明归因逻辑
- 给出处置建议
- 说明升级前提
- 提供客服模板
- 提供工单字段建议

以下内容不写入 RAG，继续以结构化数据为真源：

- SLA 数值：`mock-data/carriers.json`
- 扣罚参数：`mock-data/fee_rules.json`
- 运费重算结果与账单差额：`mock-data/settlement_bills.json`、`mock-data/fee_rules.json`、`mock-data/packages.json`
- 计费重与偏远地区标记：`mock-data/packages.json`
- 签收状态与签收凭证：`mock-data/shipments.json`
- 轨迹时间线：`mock-data/tracking_events.json`
- 库存与锁库结果：`mock-data/inventory.json`、`mock-data/inventory_locks.json`
- 仓内节点与出库状态：`mock-data/warehouse_tasks.json`、`mock-data/outbound_records.json`
- 赔付金额与证据状态：`mock-data/compensation_cases.json`
- 工单实时状态：`mock-data/exception_tickets.json`

## 来源口径

- 场景、字段、责任部门：`docs/Canonical Matrix.md`
- 知识库拆分与路由：`docs/RAG Design.md`
- 智能体路由与输出边界：`docs/Agent Design.md`
- Demo 对应关系：`mock-data/demo_cases.json`
- 结构化事实真源：`mock-data/`
