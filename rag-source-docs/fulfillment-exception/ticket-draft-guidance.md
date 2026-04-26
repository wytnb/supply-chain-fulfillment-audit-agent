# 规则编号：FE-006
# 规则名称：异常工单草稿与流转建议规则
# 知识库：kb_fulfillment_exception_rules
# 适用场景：ticket_draft_and_tracking
# 适用角色：customer_service、warehouse_operator、logistics、finance、manual_review
# 规则版本：v1.0
# 是否模拟规则：true
# 关联测试编号：RAG-EXT-003

## 规则摘要
本规则用于统一异常工单草稿应包含哪些字段、何时刷新旧工单、何时升级而不是重复建单。  
在当前项目里，工单能力被定义为“草稿生成与处理跟踪建议”，而不是正式闭环结单。因此，本规则重点解决两个问题：一是不同异常场景要怎样把结构化事实转成一张可交接的草稿；二是工单如何持续补充处理记录，避免客服、仓库、物流和财务各自创建平行工单。  
本规则不定义业务终态，不执行正式派单和关闭，只提供草稿字段和流转建议。

## 触发条件
- 任一异常场景需要人工继续跟进。
- 系统已识别异常类型，但需要沉淀成可交接记录。
- 已存在开放工单，需要判断是否刷新原工单而不是重复建单。
- 客户已投诉、需跨团队协作或需保留结算留痕。
- 需要给 A08 或 Ticket MCP 工具提供结构化草稿输入。

## 需要查询的数据
- `exception_tickets.json`：确认是否已有工单、当前状态和历史处理记录。
- `orders.json` / `shipments.json`：确认业务对象是订单还是运单。
- 各场景对应的结构化事实源：如 `warehouse_tasks.json`、`inventory_locks.json`、`tracking_events.json`、`settlement_bills.json`、`compensation_cases.json`。
- `demo_cases.json`：确认场景与预期输出关系，保证草稿字段与主案例一致。

## 判断逻辑
- 第一步，先确认场景主键。订单型异常至少要锁定 `order_no`，运单型异常至少要锁定 `waybill_no`；涉及账单时还应附带 `carrier_bill_amount` 或账单号。
- 第二步，优先查询是否已有同对象、同异常类型的开放工单。若已存在，优先刷新，不重复新建。
- 第三步，工单草稿必须包含最小判断结果：`scenario_code`、`exception_type`、`responsible_department`、建议动作、关键证据摘要。
- 第四步，建议动作只能写“核查、催办、补证、复算、升级确认”这类可执行动作，不写成最终业务结论。
- 第五步，若多个异常并发，例如轨迹停滞同时涉及账单扣罚，则工单可保留主异常和次级结算字段，但不要把所有结论混成一个不可维护的文本块。
- 第六步，正式关闭、最终赔付、最终扣罚、正式派单不在本规则范围内。

## 责任归因
- `warehouse`：处理仓内超时、拣货积压、出库阻塞。
- `inventory_planning`：处理锁库失败、库存不足、调拨评估。
- `logistics`：处理轨迹停滞、承运商催办、运输异常跟进。
- `finance`：处理账单差异、扣罚审核、赔付结算承接。
- `manual_review`：处理证据冲突、多异常并发或高风险争议。

## 处理建议
- 草稿标题建议包含“异常类型 + 业务对象 + 当前卡点”，例如“轨迹停滞工单草稿 - WB-XXXX - 最后停留转运节点”。
- 草稿正文建议分为四段：事实摘要、责任部门、建议动作、待补证据。
- 建议动作应控制在 2 到 4 条，避免写成泛化空话。
- 每次刷新工单时追加新的处理记录，不覆盖旧记录，以便回溯。
- 跨团队流转时要保留下一次回查时间、当前责任方和待补信息，减少空转。

## 升级条件
- 已存在工单但长时间无更新。
- 客户投诉升级，需要主管或人工复核介入。
- 结构化事实冲突，单一责任部门无法独立处理。
- 同一对象出现多重异常，需要跨团队协同。
- 结算或赔付事项准备落账，但业务证据仍不完整。

## 工单字段建议
- 公共字段：`ticket_no`、`order_no`、`waybill_no`、`scenario_code`、`exception_type`、`responsible_department`、`ticket_status`
- 事实字段：当前卡点、最后更新时间、关键异常摘要、结构化证据来源
- 动作字段：`suggested_actions`、下一次回查时间、需协同团队
- 场景附加字段：
- `late_shipment`：`promise_ship_deadline`、`warehouse_status`、`current_node`
- `inventory_shortage`：`sku_code`、`shortage_qty`、`lock_failed_reason`
- `tracking_stagnation`：最后轨迹时间、最后轨迹类型、承运商反馈摘要
- `abnormal_signed`：`signed_by`、`signed_proof_type`、`evidence_status`
- `freight_bill_audit`：`carrier_bill_amount`、重算摘要、差异原因分类
