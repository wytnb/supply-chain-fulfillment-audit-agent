# MCP 工具设计 / MCP Design

## 文档定位

本文档定义 5 类 MCP 工具的统一契约、工具目录、状态、调用者和数据来源。

本文档不负责：

- 业务范围定义。
- Mock 数据样例内容。
- 智能体提示词。

共享字段和工具状态口径以 [Canonical Matrix](./Canonical%20Matrix.md) 为准。

---

## 1. 总体设计

### 1.1 Server 定位

```text
supplychain-fulfillment-mcp-server
```

### 1.2 总体原则

|原则|说明|
|---|---|
|结构化事实优先|工具返回订单、库存、轨迹、账单等事实数据|
|结构化数值优先|SLA 数值、费用和计费重以结构化数据为准|
|RAG 只做规则解释|RAG 不直接产出数值，不替代工具|
|默认只读|除工单草稿外，MVP 工具不做真实写入|
|统一返回结构|所有工具返回 `success`、`code`、`message`、`data`、`trace`|

### 1.3 通用请求字段

```json
{
  "request_id": "REQ-20260426-000001",
  "trace_id": "TRACE-20260426-000001",
  "operator_role": "customer_service",
  "operator_id": "demo_user_001",
  "need_masking": true
}
```

### 1.4 通用响应结构

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {},
  "trace": {
    "source_system": "mock_wms",
    "record_id": "WT-202604240003",
    "snapshot_time": "2026-04-26T10:30:00+08:00"
  }
}
```

### 1.5 通用错误码

|错误码|说明|
|---|---|
|`INVALID_ARGUMENT`|缺少必要入参或字段格式不正确|
|`NOT_FOUND`|未找到对应订单、运单、账单或工单|
|`DATA_CONFLICT`|不同结构化来源存在冲突，无法直接下结论|
|`RULE_NOT_APPLICABLE`|规则不适用或条件不足|
|`RESERVED_TOOL`|工具被保留但未纳入 MVP 调用|

---

## 2. 工具目录

### 2.1 MVP 可调用工具

|工具名|域|状态|调用方|主要数据来源|覆盖 Demo|
|---|---|---|---|---|---|
|`oms_get_order_detail`|OMS|mvp|A02|`orders.json`|D01 D02 D04|
|`oms_get_order_status`|OMS|mvp|A02|`orders.json`|D01 D02|
|`oms_get_payment_status`|OMS|mvp|A02|`orders.json`|D01 D02|
|`oms_get_order_address`|OMS|mvp|A02|`orders.json`|D04|
|`oms_get_order_items`|OMS|mvp|A02 A06|`order_items.json`|D02 D05|
|`wms_get_inventory_snapshot`|WMS|mvp|A03|`inventory.json`|D01 D02|
|`wms_get_inventory_lock_detail`|WMS|mvp|A03|`inventory_locks.json`|D01 D02|
|`wms_get_order_warehouse_progress`|WMS|mvp|A04|`warehouse_tasks.json`|D01|
|`wms_get_outbound_record`|WMS|mvp|A04|`outbound_records.json`|D01 D02|
|`wms_check_fulfillment_blockers`|WMS|mvp|A04|`warehouse_tasks.json` + `outbound_records.json`|D01|
|`tms_get_waybill_by_order`|TMS|mvp|A05|`shipments.json`|D04|
|`tms_get_shipment_detail`|TMS|mvp|A05|`shipments.json`|D03 D04 D05|
|`tms_get_tracking_events`|TMS|mvp|A05|`tracking_events.json`|D03 D04|
|`tms_get_delivery_status`|TMS|mvp|A05|`shipments.json`|D04|
|`tms_get_carrier_profile`|TMS|mvp|A05 A06|`carriers.json`|D03 D05|
|`tms_check_tracking_stagnation`|TMS|mvp|A05|`tracking_events.json` + `carriers.json`|D03|
|`settlement_calculate_freight`|Settlement|mvp|A06|`packages.json` + `fee_rules.json`|D05|
|`settlement_get_fee_breakdown`|Settlement|mvp|A06|`packages.json` + `fee_rules.json`|D05|
|`settlement_calculate_timeout_penalty`|Settlement|mvp|A06|`shipments.json` + `carriers.json` + `fee_rules.json`|D03|
|`settlement_calculate_compensation`|Settlement|mvp|A06|`compensation_cases.json` + `orders.json` + `shipments.json`|D04|
|`settlement_audit_carrier_bill`|Settlement|mvp|A06|`settlement_bills.json` + `packages.json` + `fee_rules.json`|D05|
|`ticket_create_exception_ticket`|Ticket|mvp|A08|`exception_tickets.json`|D01 D02 D03 D04 D05|
|`ticket_get_ticket_status`|Ticket|mvp|A08|`exception_tickets.json`|D01 D02 D03 D04 D05|
|`ticket_append_process_record`|Ticket|mvp|A08|`exception_tickets.json`|横切能力|
|`ticket_list_by_order`|Ticket|mvp|A01 A08|`exception_tickets.json`|横切能力|

### 2.2 Reserved 工具

以下工具保留名称，但不纳入 MVP 案例链路：

|工具名|状态|原因|
|---|---|---|
|`oms_get_fulfillment_summary`|reserved|可由 `oms_get_order_detail` 聚合替代|
|`ticket_close_ticket`|reserved|MVP 不支持人工终态结单|

---

## 3. 工具契约

以下只定义 MVP 可调用工具。

### 3.1 `oms_get_order_detail`

|项目|内容|
|---|---|
|用途|查询订单基础事实|
|必要入参|`order_no`|
|主要出参|`order_no`、`order_status`、`payment_status`、`fulfillment_status`、`promise_ship_deadline`、`warehouse_code`、`carrier_code`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A02|

### 3.2 `oms_get_order_status`

|项目|内容|
|---|---|
|用途|查询订单状态时间线|
|必要入参|`order_no`|
|主要出参|`order_status`、`fulfillment_status`、`cancel_status`、`order_status_timeline`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A02|

### 3.3 `oms_get_payment_status`

|项目|内容|
|---|---|
|用途|查询支付状态|
|必要入参|`order_no`|
|主要出参|`payment_status`、`paid_time`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A02|

### 3.4 `oms_get_order_address`

|项目|内容|
|---|---|
|用途|查询脱敏收货地址|
|必要入参|`order_no`|
|主要出参|`province`、`city`、`district`、`address_detail_masked`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A02|

### 3.5 `oms_get_order_items`

|项目|内容|
|---|---|
|用途|查询订单商品明细|
|必要入参|`order_no`|
|主要出参|`items`，包含 `sku_code`、`sku_name`、`qty`、`unit_price`、`line_amount`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A02、A06|

### 3.6 `wms_get_inventory_snapshot`

|项目|内容|
|---|---|
|用途|查询库存快照|
|必要入参|`sku_code`、`warehouse_code`|
|主要出参|`available_qty`、`locked_qty`、`on_hand_qty`、`inventory_status`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A03|

### 3.7 `wms_get_inventory_lock_detail`

|项目|内容|
|---|---|
|用途|查询锁库记录|
|必要入参|`order_no`|
|主要出参|`lock_status`、`required_qty`、`locked_qty`、`shortage_qty`、`lock_failed_reason`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A03|

### 3.8 `wms_get_order_warehouse_progress`

|项目|内容|
|---|---|
|用途|查询仓储任务进度|
|必要入参|`order_no`|
|主要出参|`warehouse_status`、`current_node`、`current_owner`、`last_update_time`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A04|

### 3.9 `wms_get_outbound_record`

|项目|内容|
|---|---|
|用途|查询出库记录|
|必要入参|`order_no`|
|主要出参|`outbound_status`、`outbound_no`、`outbound_time`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A04|

### 3.10 `wms_check_fulfillment_blockers`

|项目|内容|
|---|---|
|用途|归纳仓内阻塞点|
|必要入参|`order_no`|
|主要出参|`has_exception`、`exception_type`、`exception_reason`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A04|

### 3.11 `tms_get_waybill_by_order`

|项目|内容|
|---|---|
|用途|根据订单号查询运单|
|必要入参|`order_no`|
|主要出参|`waybill_no`、`ship_time`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A05|

### 3.12 `tms_get_shipment_detail`

|项目|内容|
|---|---|
|用途|查询运单详情|
|必要入参|`waybill_no`|
|主要出参|`carrier_code`、`service_level`、`shipment_status`、`ship_time`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A05|

### 3.13 `tms_get_tracking_events`

|项目|内容|
|---|---|
|用途|查询轨迹事件列表|
|必要入参|`waybill_no`|
|主要出参|`tracking_events`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A05|

### 3.14 `tms_get_delivery_status`

|项目|内容|
|---|---|
|用途|查询签收状态|
|必要入参|`waybill_no`|
|主要出参|`delivery_status`、`signed_time`、`signed_by`、`signed_proof_type`、`signed_proof_url`、`abnormal_reason`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A05|

### 3.15 `tms_get_carrier_profile`

|项目|内容|
|---|---|
|用途|查询承运商结构化 SLA 和服务能力|
|必要入参|`carrier_code`、`service_level`|
|主要出参|`carrier_name`、`default_sla_hours`、`remote_area_extra_hours`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A05、A06|

### 3.16 `tms_check_tracking_stagnation`

|项目|内容|
|---|---|
|用途|按结构化 SLA 判断轨迹停滞|
|必要入参|`waybill_no`|
|主要出参|`is_stagnated`、`hours_since_last_event`、`stagnation_threshold_hours`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A05|

### 3.17 `settlement_calculate_freight`

|项目|内容|
|---|---|
|用途|重算基础运费|
|必要入参|`waybill_no`|
|主要出参|`chargeable_weight_kg`、`system_calculated_amount`、`fee_breakdown`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`、`DATA_CONFLICT`|
|调用方|A06|

### 3.18 `settlement_get_fee_breakdown`

|项目|内容|
|---|---|
|用途|输出详细计费拆分|
|必要入参|`waybill_no`|
|主要出参|`weight_calculation`、`value_added_services`、`fee_breakdown`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A06|

### 3.19 `settlement_calculate_timeout_penalty`

|项目|内容|
|---|---|
|用途|计算超时扣罚建议|
|必要入参|`waybill_no`|
|主要出参|`is_timeout`、`timeout_hours`、`penalty_amount`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A06|

### 3.20 `settlement_calculate_compensation`

|项目|内容|
|---|---|
|用途|计算赔付建议金额|
|必要入参|`order_no` 或 `waybill_no`、`exception_type`|
|主要出参|`is_compensable`、`compensation_amount`、`manual_confirm_required`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`、`RULE_NOT_APPLICABLE`|
|调用方|A06|

### 3.21 `settlement_audit_carrier_bill`

|项目|内容|
|---|---|
|用途|审核承运商账单金额|
|必要入参|`waybill_no`、`carrier_bill_amount`|
|主要出参|`system_calculated_amount`、`carrier_bill_amount`、`difference_amount`、`difference_reasons`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`、`DATA_CONFLICT`|
|调用方|A06|

### 3.22 `ticket_create_exception_ticket`

|项目|内容|
|---|---|
|用途|创建异常工单草稿|
|必要入参|`exception_type`、`responsible_department`、`suggested_actions`|
|主要出参|`ticket_no`、`ticket_status`、`create_as_draft`|
|错误码|`INVALID_ARGUMENT`|
|调用方|A08|

### 3.23 `ticket_get_ticket_status`

|项目|内容|
|---|---|
|用途|查询工单状态|
|必要入参|`ticket_no`|
|主要出参|`ticket_status`、`current_owner`、`process_records`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A08|

### 3.24 `ticket_append_process_record`

|项目|内容|
|---|---|
|用途|追加处理记录|
|必要入参|`ticket_no`、`record_time`、`record_content`|
|主要出参|`record_appended`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A08|

### 3.25 `ticket_list_by_order`

|项目|内容|
|---|---|
|用途|查询订单关联工单|
|必要入参|`order_no`|
|主要出参|`tickets`，包含 `ticket_no`、`ticket_status`、`exception_type`|
|错误码|`INVALID_ARGUMENT`、`NOT_FOUND`|
|调用方|A01、A08|

---

## 4. 与智能体和数据的关系

### 4.1 Agent 与工具映射

|智能体|工具|
|---|---|
|A02|`oms_get_order_detail`、`oms_get_order_status`、`oms_get_payment_status`、`oms_get_order_address`、`oms_get_order_items`|
|A03|`wms_get_inventory_snapshot`、`wms_get_inventory_lock_detail`|
|A04|`wms_get_order_warehouse_progress`、`wms_get_outbound_record`、`wms_check_fulfillment_blockers`|
|A05|`tms_get_waybill_by_order`、`tms_get_shipment_detail`、`tms_get_tracking_events`、`tms_get_delivery_status`、`tms_get_carrier_profile`、`tms_check_tracking_stagnation`|
|A06|`settlement_calculate_freight`、`settlement_get_fee_breakdown`、`settlement_calculate_timeout_penalty`、`settlement_calculate_compensation`、`settlement_audit_carrier_bill`|
|A08|`ticket_create_exception_ticket`、`ticket_get_ticket_status`、`ticket_append_process_record`、`ticket_list_by_order`|

### 4.2 结构化数据优先级

|主题|唯一结构化来源|RAG 角色|
|---|---|---|
|SLA 数值|`carriers.json`|解释时效规则和升级前提|
|计费重量与包裹尺寸|`packages.json`|解释计费规则|
|账单金额|`settlement_bills.json` 中的 `carrier_bill_amount`|解释差异规则|
|签收状态与凭证|`shipments.json`|解释异常签收规则|

---

## 5. 验收标准

|项|标准|
|---|---|
|工具完整性|所有 MVP 工具都有完整契约|
|字段一致性|`carrier_bill_amount` 等共享字段与 Mock Data Design 一致|
|案例覆盖|5 个 MVP demo 所需工具全部为 `mvp` 状态|
|边界控制|`ticket_close_ticket` 仍为 `reserved`，不进入 MVP 案例链路|
