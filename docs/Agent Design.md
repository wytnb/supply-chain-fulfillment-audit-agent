# 多智能体设计 / Agent Design

## 文档定位

本文档负责定义智能体清单、职责边界、共享输入输出、知识库路由和 5 个 MVP 主演示案例的调用链。

本文档不负责：

- 项目范围和成功标准。
- MCP 工具字段级真源。
- Mock Data 具体数据文件结构。

共享术语、字段和案例名称统一引用 [Canonical Matrix](./Canonical%20Matrix.md)。

---

## 1. 总体设计

### 1.1 总体目标

智能体层不直接替代业务系统，不执行真实退款、赔付、扣款、正式派单或人工终态结单。其核心作用是：

|能力|说明|
|---|---|
|意图识别|识别用户是查订单、库存、物流、费用，还是需要生成工单草稿|
|任务拆解|把复杂异常拆成订单、库存、仓储、运输、规则、结算、工单子任务|
|工具调用|根据场景调用 OMS、WMS、TMS、Settlement、Ticket 工具|
|规则引用|通过 A07 检索知识库，为结论提供规则依据|
|结果汇总|输出原因分析、责任判断、处理建议、客服回复建议和工单草稿|
|风险控制|高风险结论只生成建议，必须提示人工确认|

### 1.2 智能体清单

|编号|智能体|核心职责|是否 MVP 核心|
|---|---|---|---|
|A01|主调度智能体|识别意图、拆解任务、汇总最终结果|是|
|A02|订单履约智能体|查询订单事实、订单状态、支付状态、地址和商品|是|
|A03|库存智能体|查询库存、锁库、缺货和调拨相关事实|是|
|A04|仓储作业智能体|查询拣货、复核、打包、出库和仓内阻塞点|是|
|A05|运输轨迹智能体|查询运单、轨迹、签收状态和承运商信息|是|
|A06|费用结算智能体|计算运费、扣罚、赔付建议金额和账单差异|是|
|A07|规则检索智能体|按场景路由知识库并返回规则摘要|是|
|A08|工单生成智能体|生成异常工单草稿和处理跟踪建议|是|

客服回复不是独立智能体。MVP 统一定义为：**A01 主调度结合 A07 检索结果，在 workflow 输出节点生成客服回复建议。**

### 1.3 调用原则

|原则|说明|
|---|---|
|先事实，后规则|先取结构化事实，再检索知识库解释|
|先定位，再建议|先判断异常类型和责任部门，再输出建议|
|先只读，后草稿|默认只做查询与分析，写入只创建工单草稿|
|结构化数值优先|SLA 数值、费用、计费重以结构化数据为准，RAG 只做规则解释|
|高风险人工确认|赔付、扣罚、退款、正式派单和人工终态结单必须人工确认|

---

## 2. 共享输入输出

### 2.1 共享输入结构

```json
{
  "user_query": "订单 ORD202604240003 为什么还没发货",
  "intent_code": "late_shipment_diagnosis",
  "scenario_code": "late_shipment",
  "operator_role": "customer_service",
  "business_object": {
    "order_no": "ORD202604240003",
    "waybill_no": null,
    "carrier_bill_amount": null
  },
  "expected_outputs": [
    "root_cause_analysis",
    "responsible_department",
    "suggested_actions",
    "customer_reply",
    "ticket_draft"
  ],
  "trace_id": "TRACE-20260426-000001"
}
```

### 2.2 子智能体共享输出结构

```json
{
  "agent_name": "warehouse_operation_agent",
  "scenario_code": "late_shipment",
  "facts_summary": [
    "仓库拣货任务超时 24 小时"
  ],
  "exception_type": "picking_timeout",
  "responsible_department": "warehouse",
  "suggested_actions": [
    "仓库优先核查拣货任务状态"
  ],
  "evidence": [
    {
      "source": "wms_get_order_warehouse_progress",
      "record_id": "WT-202604240003"
    }
  ]
}
```

### 2.3 统一枚举引用

本文档统一使用以下标准字段：

- `intent_code`
- `scenario_code`
- `exception_type`
- `responsible_department`
- `carrier_bill_amount`

不再使用 `responsible_party` 作为对外共享字段。

---

## 3. A01 主调度智能体

### 3.1 定位

A01 负责识别意图、确定场景、决定调用哪些子智能体，并合并最终业务结论。

### 3.2 路由规则

|输入特征|`intent_code`|`scenario_code`|调用智能体|
|---|---|---|---|
|订单号 + 没发货 / 超时 / 待发货|`late_shipment_diagnosis`|`late_shipment`|A02、A03、A04、A07、A08|
|订单号 + 缺货 / 发不了|`inventory_shortage_check`|`inventory_shortage`|A02、A03、A07、A08|
|运单号 + 不动 / 延误|`tracking_stagnation_check`|`tracking_stagnation`|A05、A06、A07、A08|
|订单号或运单号 + 已签收未收到|`abnormal_signed_check`|`abnormal_signed`|A02、A05、A06、A07、A08|
|运单号 + 账单金额 / 运费差异|`freight_bill_audit`|`freight_bill_audit`|A05、A06、A07、A08|
|破损 / 丢件 / 赔付|`damage_or_loss_compensation_check`|`damage_or_loss_compensation`|A02、A05、A06、A07、A08|

### 3.3 输出模板

```markdown
## 处理结论
- 场景：`scenario_code`
- 异常类型：`exception_type`
- 责任部门：`responsible_department`

## 关键依据
- 结构化事实
- 规则编号

## 处理建议
- 建议 1
- 建议 2

## 客服回复建议
- 面向客户的解释模板

## 工单草稿
- 若需人工处理，则输出工单标题、优先级、建议动作和所需证据
```

---

## 4. 专业子智能体

### 4.1 A02 订单履约智能体

|项目|内容|
|---|---|
|主要职责|查询订单详情、订单状态、支付状态、地址和订单商品|
|主要工具|`oms_get_order_detail`、`oms_get_order_status`、`oms_get_payment_status`、`oms_get_order_address`、`oms_get_order_items`|
|输出重点|订单是否有效、是否已支付、是否已取消、订单维度基础事实|

### 4.2 A03 库存智能体

|项目|内容|
|---|---|
|主要职责|查询库存快照、锁库状态、缺货和调拨可行性|
|主要工具|`wms_get_inventory_snapshot`、`wms_get_inventory_lock_detail`|
|说明|`inventory` 统一定义为 WMS 域内能力，不作为独立 MCP 域|

### 4.3 A04 仓储作业智能体

|项目|内容|
|---|---|
|主要职责|查询拣货、复核、打包、出库和仓内阻塞点|
|主要工具|`wms_get_order_warehouse_progress`、`wms_get_outbound_record`、`wms_check_fulfillment_blockers`|
|输出重点|是否仓库处理超时、是否存在仓内阻塞、是否已出库|

### 4.4 A05 运输轨迹智能体

|项目|内容|
|---|---|
|主要职责|查询运单详情、轨迹、签收状态和承运商信息|
|主要工具|`tms_get_waybill_by_order`、`tms_get_shipment_detail`、`tms_get_tracking_events`、`tms_get_delivery_status`、`tms_get_carrier_profile`、`tms_check_tracking_stagnation`|
|输出重点|是否已发货、是否轨迹停滞、是否异常签收、最后轨迹时间|

### 4.5 A06 费用结算智能体

|项目|内容|
|---|---|
|主要职责|计算运费、扣罚、赔付建议金额和账单差异|
|主要工具|`settlement_calculate_freight`、`settlement_get_fee_breakdown`、`settlement_calculate_timeout_penalty`、`settlement_calculate_compensation`、`settlement_audit_carrier_bill`|
|输出重点|系统重算金额、差异原因、扣罚建议、赔付建议金额|

### 4.6 A07 规则检索智能体

|项目|内容|
|---|---|
|主要职责|按场景路由知识库，返回规则编号、摘要和适用前提|
|主要输出|规则编号、规则摘要、适用条件、禁用表达|
|说明|不直接产出数值型 SLA 和费用结果|

### 4.7 A08 工单生成智能体

|项目|内容|
|---|---|
|主要职责|生成工单草稿和处理跟踪建议|
|主要工具|`ticket_create_exception_ticket`、`ticket_get_ticket_status`、`ticket_append_process_record`、`ticket_list_by_order`|
|边界|不正式派单，不做人工终态结单|

---

## 5. 知识库路由

统一采用两层路由：`判责路由` 与 `对客回复路由`。

|`scenario_code`|判责路由|对客回复路由|
|---|---|---|
|`late_shipment`|`kb_fulfillment_exception_rules`、`kb_warehouse_operation_sop`|按需追加 `kb_customer_service_templates`|
|`inventory_shortage`|`kb_fulfillment_exception_rules`|按需追加 `kb_customer_service_templates`|
|`tracking_stagnation`|`kb_carrier_sla_rules`、`kb_fulfillment_exception_rules`|按需追加 `kb_customer_service_templates`|
|`abnormal_signed`|`kb_fulfillment_exception_rules`、`kb_carrier_sla_rules`、`kb_freight_settlement_rules`|`kb_customer_service_templates`|
|`damage_or_loss_compensation`|`kb_freight_settlement_rules`、`kb_carrier_sla_rules`，必要时追加 `kb_fulfillment_exception_rules`|`kb_customer_service_templates`|
|`freight_bill_audit`|`kb_freight_settlement_rules`、`kb_carrier_sla_rules`|通常无需对客回复|

---

## 6. 5 个 MVP 主演示案例调用链

案例定义以 [Canonical Matrix](./Canonical%20Matrix.md) 的 MVP demo 表为准。

### 6.1 D01 订单超时未发货

```text
用户输入 order_no
→ A01 主调度
→ A02 订单履约
→ A03 库存
→ A04 仓储作业
→ A07 规则检索
→ A08 工单生成
→ A01 汇总输出
```

### 6.2 D02 库存不足导致无法发货

```text
用户输入 order_no
→ A01 主调度
→ A02 订单履约
→ A03 库存
→ A07 规则检索
→ A08 工单生成
→ A01 汇总输出
```

### 6.3 D03 承运商运输延误 / 轨迹停滞

```text
用户输入 waybill_no
→ A01 主调度
→ A05 运输轨迹
→ A06 费用结算
→ A07 规则检索
→ A08 工单生成
→ A01 汇总输出
```

### 6.4 D04 客户反馈已签收未收到货

```text
用户输入 order_no 或 waybill_no
→ A01 主调度
→ A02 订单履约
→ A05 运输轨迹
→ A06 费用结算
→ A07 规则检索
→ A08 工单生成
→ A01 汇总输出
```

### 6.5 D05 运费结算审核

```text
用户输入 waybill_no + carrier_bill_amount
→ A01 主调度
→ A05 运输轨迹
→ A06 费用结算
→ A07 规则检索
→ A08 工单生成
→ A01 汇总输出
```

---

## 7. 风险控制

|场景|禁止输出|正确输出|
|---|---|---|
|赔付|“直接执行赔付”|“根据模拟规则建议赔付 X 元，需人工确认”|
|扣罚|“直接扣承运商款”|“满足模拟扣罚条件，建议财务复核后处理”|
|退款|“已退款”|“建议进入退款审核流程”|
|工单|“已正式派单”|“已生成工单草稿，需人工确认派发”|
|关闭工单|“已闭环”|“可追加处理记录，终态结单需人工执行”|

---

## 8. 验收标准

|模块|验收标准|
|---|---|
|智能体完整性|A01-A08 职责和边界清晰|
|案例一致性|5 个 MVP demo 名称和调用链与 Canonical Matrix 一致|
|MCP 协同|各智能体调用的工具在 MCP Design 中有完整契约|
|RAG 协同|每个场景的知识库路由与 RAG Design 一致|
|客服输出|客服回复由 A01 + A07 生成，不出现单独客服智能体角色|
|边界控制|全文不出现正式派单、人工终态结单、直接执行赔付等越界表述|
