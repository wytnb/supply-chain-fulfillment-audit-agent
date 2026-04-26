# RAG 设计 / RAG Design

## 文档定位

本文档定义知识库拆分、路由策略、规则文档格式和测试用例分层。

本文档不负责：

- 项目范围和成功标准。
- 结构化数据字段真源。
- MCP 工具契约。

场景编码、异常类型和 Demo 名称统一引用 [Canonical Matrix](./Canonical%20Matrix.md)。

---

## 1. 知识库设计

### 1.1 知识库清单

|知识库|Dify 名称|作用|
|---|---|---|
|履约异常处理知识库|`kb_fulfillment_exception_rules`|解释异常类型、责任归因和处理动作|
|仓储作业 SOP 知识库|`kb_warehouse_operation_sop`|解释仓内流程、仓库责任和操作建议|
|承运商 SLA 知识库|`kb_carrier_sla_rules`|解释时效标准、升级条件和扣罚前提|
|运费结算规则知识库|`kb_freight_settlement_rules`|解释运费、扣罚、赔付和账单差异|
|客服话术知识库|`kb_customer_service_templates`|生成面向客户的回复模板和禁用表达|

### 1.2 统一原则

|原则|说明|
|---|---|
|RAG 只解释规则|不直接产出数值型 SLA、重量、费用|
|先结构化事实，再检索规则|避免规则脱离数据上下文|
|两层路由|统一分为判责路由和对客回复路由|
|输出要可引用|返回规则编号、摘要和适用条件|

---

## 2. 规则文档格式

### 2.1 通用模板

```markdown
# 规则编号：FE-001
# 规则名称：订单超时未发货处理规则
# 适用场景：late_shipment
# 适用角色：customer_service, warehouse_operator
# 规则版本：v1.0
# 是否模拟规则：true

## 规则摘要
## 触发条件
## 需要查询的数据
## 判断逻辑
## 责任归因
## 处理建议
## 升级条件
## 客服表达建议
## 工单字段建议
```

### 2.2 推荐元数据

|字段|说明|
|---|---|
|`kb_type`|知识库类型|
|`rule_id`|规则编号|
|`scenario_code`|业务场景编码|
|`exception_type`|异常类型|
|`role`|适用角色|
|`version`|规则版本|
|`is_mock_rule`|是否模拟规则|

---

## 3. 路由策略

### 3.1 判责路由

|`scenario_code`|知识库|
|---|---|
|`late_shipment`|`kb_fulfillment_exception_rules`、`kb_warehouse_operation_sop`|
|`inventory_shortage`|`kb_fulfillment_exception_rules`|
|`tracking_stagnation`|`kb_carrier_sla_rules`、`kb_fulfillment_exception_rules`|
|`abnormal_signed`|`kb_fulfillment_exception_rules`、`kb_carrier_sla_rules`、`kb_freight_settlement_rules`|
|`damage_or_loss_compensation`|`kb_freight_settlement_rules`、`kb_carrier_sla_rules`，必要时追加 `kb_fulfillment_exception_rules`|
|`freight_bill_audit`|`kb_freight_settlement_rules`、`kb_carrier_sla_rules`|

### 3.2 对客回复路由

|`scenario_code`|知识库|
|---|---|
|`late_shipment`|按需追加 `kb_customer_service_templates`|
|`inventory_shortage`|按需追加 `kb_customer_service_templates`|
|`tracking_stagnation`|`kb_customer_service_templates`|
|`abnormal_signed`|`kb_customer_service_templates`|
|`damage_or_loss_compensation`|`kb_customer_service_templates`|
|`freight_bill_audit`|通常无需对客回复|

### 3.3 赔付场景固定规则

赔付类场景统一采用以下顺序：

1. 判责必查 `kb_freight_settlement_rules` 与 `kb_carrier_sla_rules`。
2. 需要补充异常归因时，再查 `kb_fulfillment_exception_rules`。
3. 需要输出客服回复时，再查 `kb_customer_service_templates`。

---

## 4. 与智能体协同

|智能体|RAG 角色|
|---|---|
|A01|汇总规则依据，生成最终解释和客服回复|
|A04|读取仓储 SOP 解释仓内处理节点|
|A05|读取 SLA 解释时效和升级前提|
|A06|读取结算规则解释费用和赔付|
|A07|统一负责知识库路由、规则检索和规则摘要输出|

---

## 5. 测试用例分层

### 5.1 MVP 5 例

|测试编号|场景|期望知识库|说明|
|---|---|---|---|
|`RAG-MVP-001`|`late_shipment`|履约异常 + 仓储 SOP|解释超时未发货与仓内责任|
|`RAG-MVP-002`|`inventory_shortage`|履约异常|解释缺货、锁库失败和调拨建议|
|`RAG-MVP-003`|`tracking_stagnation`|承运商 SLA + 履约异常|解释轨迹停滞与升级条件|
|`RAG-MVP-004`|`abnormal_signed`|履约异常 + 承运商 SLA + 客服话术|解释异常签收、举证和对客回复|
|`RAG-MVP-005`|`freight_bill_audit`|运费结算规则 + 承运商 SLA|解释账单差异和异议建议|

### 5.2 扩展验证

|测试编号|场景|期望知识库|说明|
|---|---|---|---|
|`RAG-EXT-001`|`damage_or_loss_compensation`|运费结算规则 + 承运商 SLA + 客服话术|商品破损是否能赔|
|`RAG-EXT-002`|`tracking_stagnation`|承运商 SLA + 运费结算规则|偏远地区配送超时是否扣罚|
|`RAG-EXT-003`|`ticket_draft_and_tracking`|履约异常 + 仓储 SOP + SLA|不同异常场景的工单字段建议|

---

## 6. 推荐目录

当前仓库内不再额外引入新的 `rag_design/` 子目录作为规范前提。建议直接围绕现有 `docs/` 维护主设计文档，并在未来需要时再新增实际使用的规则源目录，例如：

```text
docs/
├── README.md
├── Canonical Matrix.md
├── Project Brief.md
├── Agent Design.md
├── MCP Design.md
├── Mock Data Design.md
└── RAG Design.md
```

如果后续确实落地源规则文件，再新增：

```text
rag-source-docs/
├── fulfillment-exception/
├── warehouse-sop/
├── carrier-sla/
├── freight-settlement/
└── customer-service/
```

---

## 7. 验收标准

|项|标准|
|---|---|
|路由一致性|与 Agent Design 的判责路由、对客回复路由完全一致|
|范围一致性|只把 5 个 MVP 场景列为主测试例，其余放入扩展验证|
|边界一致性|不把 RAG 写成数值计算来源|
|客服定位一致性|客服能力表现为输出节点能力，不新增单独客服智能体角色|
