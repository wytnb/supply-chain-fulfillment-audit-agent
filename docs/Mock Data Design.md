# Mock Data 设计 / Mock Data Design

## 文档定位

本文档定义 Mock Data 的目录结构、数据模型、字段规范、案例配置和与 MCP 工具的对应关系。

本文档不负责：

- 业务范围和 MVP 边界。
- 工具入参出参契约细节。
- 知识库切片策略。

共享字段和文件命名口径以 [Canonical Matrix](./Canonical%20Matrix.md) 为准。

---

## 1. 设计原则

|原则|说明|
|---|---|
|服务 5 个主演示案例|所有 MVP 工具都必须能从 Mock Data 读取结果|
|字段唯一命名|跨文档共享字段只保留一个标准名|
|结构化事实优先|SLA、签收状态、账单金额、包裹计费字段都必须有结构化来源|
|足够真实但不过度复杂|支持演示与联调，不追求生产级数据规模|
|可追溯|每条关键结论都能回到数据文件和规则编号|

---

## 2. 推荐目录结构

```text
docs/
├── README.md
├── Canonical Matrix.md
├── Project Brief.md
├── Agent Design.md
├── MCP Design.md
├── Mock Data Design.md
└── RAG Design.md

mock-data/
├── README.md
├── orders.json
├── order_items.json
├── products.json
├── inventory.json
├── inventory_locks.json
├── warehouse_tasks.json
├── outbound_records.json
├── shipments.json
├── tracking_events.json
├── carriers.json
├── packages.json
├── fee_rules.json
├── settlement_bills.json
├── compensation_cases.json
├── exception_tickets.json
├── demo_cases.json
└── tool_call_logs.json
```

---

## 3. 全局字段规范

### 3.1 统一共享字段

|字段|说明|
|---|---|
|`scenario_code`|统一业务场景编码|
|`intent_code`|统一用户意图编码|
|`exception_type`|统一异常类型编码|
|`responsible_department`|统一责任部门字段|
|`carrier_bill_amount`|统一承运商账单金额字段|

### 3.2 废弃字段

|字段|处理方式|
|---|---|
|`responsible_party`|废弃，统一改为 `responsible_department`|
|`bill_amount`|废弃别名，只能在迁移说明里提及，不再作为主字段|

### 3.3 时间和脱敏规范

- 时间统一使用 ISO 8601，默认 `+08:00`。
- 姓名、手机号、地址只保留脱敏字段。
- 结构化数值字段使用 `number`，避免文本型金额和重量。

---

## 4. 数据模型总览

```text
orders
├─ order_items
├─ inventory_locks
├─ warehouse_tasks
├─ outbound_records
├─ shipments
│  └─ tracking_events
├─ settlement_bills
├─ compensation_cases
└─ exception_tickets

products
inventory
carriers
packages
fee_rules
tool_call_logs
demo_cases
```

---

## 5. 数据文件设计

### 5.1 `orders.json`

|字段|说明|
|---|---|
|`order_no`|订单号|
|`customer_name_masked`|脱敏姓名|
|`customer_phone_masked`|脱敏手机号|
|`order_status`|订单状态|
|`payment_status`|支付状态|
|`fulfillment_status`|履约状态|
|`cancel_status`|取消状态|
|`order_time`|下单时间|
|`paid_time`|支付时间|
|`promise_ship_deadline`|承诺发货时间|
|`promise_delivery_deadline`|承诺送达时间|
|`warehouse_code`|仓库编码|
|`carrier_code`|承运商编码|
|`service_level`|服务等级|
|`province` / `city` / `district`|行政区|
|`address_detail_masked`|脱敏地址|
|`order_amount`|订单金额|
|`mock_scenario_tag`|演示标签，非对外异常类型|

### 5.2 `order_items.json`

|字段|说明|
|---|---|
|`order_no`|订单号|
|`sku_code`|SKU|
|`sku_name`|商品名|
|`qty`|数量|
|`unit_price`|单价|
|`line_amount`|行金额|

### 5.3 `inventory.json`

|字段|说明|
|---|---|
|`warehouse_code`|仓库|
|`sku_code`|SKU|
|`available_qty`|可用库存|
|`locked_qty`|锁定库存|
|`on_hand_qty`|在手库存|
|`inventory_status`|库存状态|

### 5.4 `inventory_locks.json`

|字段|说明|
|---|---|
|`order_no`|订单号|
|`sku_code`|SKU|
|`lock_status`|锁库状态|
|`required_qty`|需求量|
|`locked_qty`|已锁量|
|`shortage_qty`|短缺量|
|`lock_failed_reason`|失败原因|

### 5.5 `warehouse_tasks.json`

|字段|说明|
|---|---|
|`task_no`|任务号|
|`order_no`|订单号|
|`warehouse_status`|仓储状态|
|`current_node`|当前节点|
|`current_owner`|当前责任岗|
|`last_update_time`|更新时间|
|`exception_type`|仓内异常类型|
|`exception_reason`|异常原因|

### 5.6 `outbound_records.json`

|字段|说明|
|---|---|
|`order_no`|订单号|
|`outbound_no`|出库单号|
|`outbound_status`|出库状态|
|`outbound_time`|出库时间|

### 5.7 `shipments.json`

`shipments.json` 是签收状态和签收凭证的唯一结构化来源。

|字段|说明|
|---|---|
|`waybill_no`|运单号|
|`order_no`|订单号|
|`carrier_code`|承运商编码|
|`service_level`|服务等级|
|`shipment_status`|运单状态|
|`ship_time`|发货时间|
|`delivery_status`|签收状态|
|`signed_time`|签收时间|
|`signed_by`|签收人|
|`signed_proof_type`|签收凭证类型|
|`signed_proof_url`|签收凭证链接|
|`abnormal_reason`|异常签收原因|

### 5.8 `tracking_events.json`

|字段|说明|
|---|---|
|`waybill_no`|运单号|
|`event_time`|事件时间|
|`event_type`|事件类型|
|`event_desc`|事件描述|
|`event_city`|事件城市|

### 5.9 `carriers.json`

`carriers.json` 是 SLA 数值的唯一结构化来源。

|字段|说明|
|---|---|
|`carrier_code`|承运商编码|
|`carrier_name`|承运商名称|
|`service_level`|服务等级|
|`default_sla_hours`|默认 SLA 小时|
|`remote_area_extra_hours`|偏远地区额外小时|
|`support_compensation`|是否支持赔付|

### 5.10 `packages.json`

`packages.json` 是计费和包裹字段的唯一结构化来源。

|字段|说明|
|---|---|
|`waybill_no`|运单号|
|`actual_weight_kg`|实重|
|`length_cm`|长|
|`width_cm`|宽|
|`height_cm`|高|
|`chargeable_weight_kg`|计费重|
|`is_remote_area`|是否偏远地区|
|`value_added_services`|增值服务列表|

### 5.11 `fee_rules.json`

|字段|说明|
|---|---|
|`carrier_code`|承运商|
|`service_level`|服务等级|
|`first_weight_kg`|首重|
|`first_weight_fee`|首重费|
|`additional_weight_unit_kg`|续重单位|
|`additional_weight_fee`|续重费|
|`volume_divisor`|体积重除数|
|`remote_area_fee`|偏远地区附加费|
|`timeout_grace_hours`|超时扣罚宽限小时|
|`timeout_penalty_per_hour`|超时扣罚每小时金额|
|`timeout_penalty_cap`|超时扣罚封顶金额|

### 5.12 `settlement_bills.json`

|字段|说明|
|---|---|
|`bill_no`|账单号|
|`waybill_no`|运单号|
|`carrier_code`|承运商|
|`carrier_bill_amount`|承运商账单金额|
|`billing_date`|账单日期|
|`bill_status`|账单状态|

### 5.13 `compensation_cases.json`

|字段|说明|
|---|---|
|`case_no`|赔付案例号|
|`order_no`|订单号|
|`waybill_no`|运单号|
|`exception_type`|异常类型|
|`damage_level`|破损级别|
|`evidence_status`|举证状态|
|`compensation_amount`|建议赔付金额|
|`manual_confirm_required`|是否需要人工确认|

### 5.14 `exception_tickets.json`

|字段|说明|
|---|---|
|`ticket_no`|工单号|
|`order_no`|订单号|
|`waybill_no`|运单号|
|`exception_type`|异常类型|
|`responsible_department`|责任部门|
|`ticket_status`|工单状态|
|`suggested_actions`|建议动作|
|`process_records`|处理记录|

### 5.15 `demo_cases.json`

|字段|说明|
|---|---|
|`demo_id`|Demo 编号|
|`scenario_code`|业务场景编码|
|`user_input`|演示输入|
|`expected_tools`|期望工具|
|`expected_rule_ids`|期望规则|
|`expected_outputs`|期望输出点|

### 5.16 `tool_call_logs.json`

|字段|说明|
|---|---|
|`trace_id`|调用链 ID|
|`request_id`|请求 ID|
|`step_no`|步骤号|
|`tool_name`|工具名|
|`input`|工具入参|
|`output_summary`|输出摘要|
|`success`|是否成功|
|`code`|响应码|
|`created_time`|调用时间|

---

## 6. 数据文件与 MCP 工具映射

|工具|主要数据来源|
|---|---|
|`oms_get_order_detail`|`orders.json`|
|`oms_get_order_status`|`orders.json`|
|`oms_get_payment_status`|`orders.json`|
|`oms_get_order_address`|`orders.json`|
|`oms_get_order_items`|`order_items.json`|
|`wms_get_inventory_snapshot`|`inventory.json`|
|`wms_get_inventory_lock_detail`|`inventory_locks.json`|
|`wms_get_order_warehouse_progress`|`warehouse_tasks.json`|
|`wms_get_outbound_record`|`outbound_records.json`|
|`wms_check_fulfillment_blockers`|`warehouse_tasks.json` + `outbound_records.json`|
|`tms_get_waybill_by_order`|`shipments.json`|
|`tms_get_shipment_detail`|`shipments.json`|
|`tms_get_tracking_events`|`tracking_events.json`|
|`tms_get_delivery_status`|`shipments.json`|
|`tms_get_carrier_profile`|`carriers.json`|
|`tms_check_tracking_stagnation`|`tracking_events.json` + `carriers.json`|
|`settlement_calculate_freight`|`packages.json` + `fee_rules.json`|
|`settlement_get_fee_breakdown`|`packages.json` + `fee_rules.json`|
|`settlement_calculate_timeout_penalty`|`shipments.json` + `carriers.json` + `fee_rules.json`|
|`settlement_calculate_compensation`|`compensation_cases.json` + `orders.json` + `shipments.json`|
|`settlement_audit_carrier_bill`|`settlement_bills.json` + `packages.json` + `fee_rules.json`|
|`ticket_create_exception_ticket`|`exception_tickets.json`|
|`ticket_get_ticket_status`|`exception_tickets.json`|
|`ticket_append_process_record`|`exception_tickets.json`|
|`ticket_list_by_order`|`exception_tickets.json`|

---

## 7. 5 个 MVP 主演示案例数据要求

### 7.1 D01 `late_shipment`

|对象|要求|
|---|---|
|`orders.json`|订单已支付、未取消、超过 `promise_ship_deadline`|
|`inventory_locks.json`|已锁库|
|`warehouse_tasks.json`|拣货节点超时|
|`outbound_records.json`|尚未出库|

### 7.2 D02 `inventory_shortage`

|对象|要求|
|---|---|
|`orders.json`|订单有效、待仓库处理|
|`inventory.json`|`available_qty = 0`|
|`inventory_locks.json`|`lock_status = LOCK_FAILED`|

### 7.3 D03 `tracking_stagnation`

|对象|要求|
|---|---|
|`shipments.json`|运单在途|
|`tracking_events.json`|最后轨迹时间早于当前时间阈值|
|`carriers.json`|提供结构化 SLA|
|`fee_rules.json`|提供超时扣罚规则，至少包含 `timeout_grace_hours`、`timeout_penalty_per_hour`、`timeout_penalty_cap`|

### 7.4 D04 `abnormal_signed`

|对象|要求|
|---|---|
|`shipments.json`|必须包含 `delivery_status`、`signed_proof_type`、`signed_proof_url`、`abnormal_reason`|
|`tracking_events.json`|最后事件为签收或签收前后节点|
|`compensation_cases.json`|存在异常签收对应赔付建议|

### 7.5 D05 `freight_bill_audit`

|对象|要求|
|---|---|
|`packages.json`|必须包含实重、长宽高、计费重、偏远地区标记|
|`settlement_bills.json`|必须使用 `carrier_bill_amount`|
|`fee_rules.json`|必须可重算账单金额|

---

## 8. 验收标准

|项|标准|
|---|---|
|字段一致性|`carrier_bill_amount`、`responsible_department` 等共享字段与其他文档一致|
|结构化来源完整性|SLA、签收状态、计费字段、账单金额均有唯一结构化来源|
|工具可读性|每个 MVP 工具都能找到唯一主要数据来源|
|案例可跑通|5 个 MVP demo 均能稳定触发预期输出|
