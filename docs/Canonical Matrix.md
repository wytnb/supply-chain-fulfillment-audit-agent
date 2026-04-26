# Canonical Matrix

## 文档定位

本文件是 `docs` 目录内的全局唯一口径来源。

以下内容以本文件为准：

- 业务场景与 Demo 命名
- 统一枚举
- 共享字段名
- 责任部门和工单类型

如果其他文档和本文件冲突，以本文件为准并回修其他文档。

---

## 1. 业务场景表

|场景名称|`scenario_code`|是否 MVP 场景|是否独立 Demo|说明|
|---|---|---|---|---|
|订单超时未发货|`late_shipment`|是|是|超时未出库或未发货|
|库存不足导致无法发货|`inventory_shortage`|是|是|缺货、锁库失败、库存不足|
|承运商运输延误 / 轨迹停滞|`tracking_stagnation`|是|是|运输中长时间无新轨迹或超过 SLA|
|客户反馈已签收未收到货|`abnormal_signed`|是|是|异常签收、签收后争议|
|商品破损或丢件赔付|`damage_or_loss_compensation`|是|否|扩展验证场景|
|运费结算审核|`freight_bill_audit`|是|是|重算运费、解释账单差异|
|异常工单草稿生成与处理跟踪建议|`ticket_draft_and_tracking`|是|否|横切能力，不单列为主 demo|

---

## 2. MVP Demo 表

|Demo|场景名称|`scenario_code`|输入对象|涉及智能体|涉及 MCP 工具|涉及知识库|预期输出|
|---|---|---|---|---|---|---|---|
|D01|订单超时未发货|`late_shipment`|`order_no`|A01 A02 A03 A04 A07 A08|OMS WMS Ticket|履约异常、仓储 SOP|原因分析、责任部门、客服回复建议、工单草稿|
|D02|库存不足导致无法发货|`inventory_shortage`|`order_no`|A01 A02 A03 A07 A08|OMS WMS Ticket|履约异常|缺货判断、处理建议、工单草稿|
|D03|承运商运输延误 / 轨迹停滞|`tracking_stagnation`|`waybill_no`|A01 A05 A06 A07 A08|TMS Settlement Ticket|承运商 SLA、履约异常|超时判断、催办建议、扣罚建议|
|D04|客户反馈已签收未收到货|`abnormal_signed`|`order_no` 或 `waybill_no`|A01 A02 A05 A06 A07 A08|OMS TMS Settlement Ticket|履约异常、承运商 SLA、客服话术|异常签收判断、赔付审核建议、客服回复建议|
|D05|运费结算审核|`freight_bill_audit`|`waybill_no` + `carrier_bill_amount`|A01 A05 A06 A07 A08|TMS Settlement Ticket|运费结算规则、承运商 SLA|系统重算金额、差异原因、费用异议建议|

---

## 3. 统一枚举表

### 3.1 `intent_code`

|中文含义|`intent_code`|
|---|---|
|订单超时未发货诊断|`late_shipment_diagnosis`|
|库存不足检查|`inventory_shortage_check`|
|轨迹停滞检查|`tracking_stagnation_check`|
|异常签收检查|`abnormal_signed_check`|
|破损或丢件赔付检查|`damage_or_loss_compensation_check`|
|运费账单审核|`freight_bill_audit`|

### 3.2 `exception_type`

|中文含义|`exception_type`|
|---|---|
|订单超时未发货|`order_not_shipped_timeout`|
|库存不足|`inventory_shortage`|
|拣货超时|`picking_timeout`|
|轨迹停滞|`tracking_stagnation`|
|异常签收|`abnormal_signed`|
|破损赔付审核|`damage_compensation_review`|
|丢件赔付审核|`lost_package_compensation_review`|
|运费账单差异|`freight_bill_difference`|

### 3.3 `responsible_department`

|中文含义|`responsible_department`|
|---|---|
|客服|`customer_service`|
|仓库|`warehouse`|
|库存计划 / 供应链|`inventory_planning`|
|物流 / 承运商管理|`logistics`|
|财务 / 结算|`finance`|
|待人工复核|`manual_review`|

### 3.4 `ticket_type`

|中文含义|`ticket_type`|
|---|---|
|仓库处理异常工单|`warehouse_exception_ticket`|
|库存异常工单|`inventory_exception_ticket`|
|物流异常工单|`logistics_exception_ticket`|
|异常签收工单|`abnormal_signed_ticket`|
|费用差异复核工单|`freight_audit_ticket`|

---

## 4. 统一字段表

|字段语义|标准字段名|弃用别名|说明|
|---|---|---|---|
|业务场景编码|`scenario_code`|无|跨文档统一使用|
|用户意图编码|`intent_code`|无|跨文档统一使用|
|异常类型|`exception_type`|无|跨文档统一使用|
|责任部门|`responsible_department`|`responsible_party`|外部共享字段只保留标准字段名|
|承运商账单金额|`carrier_bill_amount`|`bill_amount`|账单审核唯一标准字段|
|签收状态|`delivery_status`|无|由 `shipments.json` 提供|
|签收凭证类型|`signed_proof_type`|无|由 `shipments.json` 提供|
|签收凭证链接|`signed_proof_url`|无|由 `shipments.json` 提供|
|异常签收原因|`abnormal_reason`|无|由 `shipments.json` 提供|
|实重|`actual_weight_kg`|无|由 `packages.json` 提供|
|计费重|`chargeable_weight_kg`|无|由 `packages.json` 提供|

---

## 5. 工具状态表

|工具名|状态|备注|
|---|---|---|
|`oms_get_order_detail`|mvp|MVP 工具|
|`oms_get_order_status`|mvp|MVP 工具|
|`oms_get_payment_status`|mvp|MVP 工具|
|`oms_get_order_address`|mvp|MVP 工具|
|`oms_get_order_items`|mvp|MVP 工具|
|`wms_get_inventory_snapshot`|mvp|MVP 工具|
|`wms_get_inventory_lock_detail`|mvp|MVP 工具|
|`wms_get_order_warehouse_progress`|mvp|MVP 工具|
|`wms_get_outbound_record`|mvp|MVP 工具|
|`wms_check_fulfillment_blockers`|mvp|MVP 工具|
|`tms_get_waybill_by_order`|mvp|MVP 工具|
|`tms_get_shipment_detail`|mvp|MVP 工具|
|`tms_get_tracking_events`|mvp|MVP 工具|
|`tms_get_delivery_status`|mvp|MVP 工具|
|`tms_get_carrier_profile`|mvp|MVP 工具|
|`tms_check_tracking_stagnation`|mvp|MVP 工具|
|`settlement_calculate_freight`|mvp|MVP 工具|
|`settlement_get_fee_breakdown`|mvp|MVP 工具|
|`settlement_calculate_timeout_penalty`|mvp|MVP 工具|
|`settlement_calculate_compensation`|mvp|MVP 工具|
|`settlement_audit_carrier_bill`|mvp|MVP 工具|
|`ticket_create_exception_ticket`|mvp|MVP 工具|
|`ticket_get_ticket_status`|mvp|MVP 工具|
|`ticket_append_process_record`|mvp|MVP 工具|
|`ticket_list_by_order`|mvp|MVP 工具|
|`oms_get_fulfillment_summary`|reserved|不纳入 MVP|
|`ticket_close_ticket`|reserved|MVP 不做人为终态结单|

---

## 6. Cross-Doc 校验清单

|检查项|要求|
|---|---|
|7 个业务场景|必须在 Project Brief 中存在|
|5 个 MVP demo|必须在 Project Brief、Agent Design、MCP Design、Mock Data Design、RAG Design 中存在|
|客服能力|定义为输出节点能力，不新增单独客服智能体角色|
|工单能力|公开表述为草稿生成与处理跟踪建议，不写正式闭环|
|账单金额|统一使用 `carrier_bill_amount`|
|SLA 数值来源|统一以 `carriers.json` 为准|
|计费字段来源|统一以 `packages.json` 为准|
