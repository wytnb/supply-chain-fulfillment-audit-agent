# Mock Data README

## 目录用途

`mock-data/` 是后续 MCP mock server 的结构化数据根目录，用于支撑 5 个 MVP Demo 的固定快照演示、联调和回归测试。

时间基线固定为 `2026-04-26T10:30:00+08:00`，所有时间字段均使用 ISO 8601，并默认采用 `+08:00` 时区。

---

## 主键与关联键

|数据文件|主键或唯一键|主要关联键|
|---|---|---|
|`orders.json`|`order_no`|`warehouse_code`、`carrier_code`、`service_level`|
|`order_items.json`|`order_no` + `sku_code`|`order_no`、`sku_code`|
|`products.json`|`sku_code`|`sku_code`|
|`inventory.json`|`warehouse_code` + `sku_code`|`warehouse_code`、`sku_code`|
|`inventory_locks.json`|`order_no` + `sku_code`|`order_no`、`sku_code`|
|`warehouse_tasks.json`|`task_no`|`order_no`|
|`outbound_records.json`|`outbound_no`|`order_no`|
|`shipments.json`|`waybill_no`|`order_no`、`carrier_code`、`service_level`|
|`tracking_events.json`|`waybill_no` + `event_time`|`waybill_no`|
|`carriers.json`|`carrier_code` + `service_level`|`carrier_code`、`service_level`|
|`packages.json`|`waybill_no`|`waybill_no`|
|`fee_rules.json`|`carrier_code` + `service_level`|`carrier_code`、`service_level`|
|`settlement_bills.json`|`bill_no`|`waybill_no`、`carrier_code`|
|`compensation_cases.json`|`case_no`|`order_no`、`waybill_no`|
|`exception_tickets.json`|`ticket_no`|`order_no`、`waybill_no`|
|`demo_cases.json`|`demo_id`|`scenario_code`|
|`tool_call_logs.json`|`trace_id` + `step_no`|`request_id`、`tool_name`|

---

## 5 个 Demo 映射

|Demo|`scenario_code`|输入对象|主记录|
|---|---|---|---|
|D01|`late_shipment`|`order_no`|`O-20260420-1001`|
|D02|`inventory_shortage`|`order_no`|`O-20260424-1002`|
|D03|`tracking_stagnation`|`waybill_no`|`WB-20260422-1006`|
|D04|`abnormal_signed`|`order_no` / `waybill_no`|`O-20260424-1004` / `WB-20260424-1004`|
|D05|`freight_bill_audit`|`waybill_no` + `carrier_bill_amount`|`WB-20260423-1005`|

---

## 数据风格说明

- 主案例之外保留少量正常样本和干扰样本，避免“所有订单都异常”。
- 所有个人信息均已脱敏，不包含真实姓名、手机号和详细地址。
- 共享字段统一使用标准名：`scenario_code`、`intent_code`、`exception_type`、`responsible_department`、`carrier_bill_amount`。
- D03 扣罚规则由 `fee_rules.json` 提供，包含 `timeout_grace_hours`、`timeout_penalty_per_hour`、`timeout_penalty_cap`。
