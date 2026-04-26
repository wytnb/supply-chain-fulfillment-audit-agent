# 规则编号：FSR-FBA-003
# 规则名称：承运商账单审核规则
# 知识库：`kb_freight_settlement_rules`
# 适用场景：`freight_bill_audit`
# 适用角色：`finance`、`logistics`、`manual_review`
# 规则版本：`v1.0`
# 是否模拟规则：`true`
# 关联测试编号：`RAG-MVP-005`

## 规则摘要
本规则用于解释承运商账单审核应如何以结构化计费资料为依据完成复核，并在发现差异时输出异议建议或工单草稿。规则不把文本文档写成运费计算器，也不在正文里写具体重算金额。  
根据仓库口径，`carrier_bill_amount` 由 `settlement_bills.json` 提供，是账单审核唯一标准字段；计费相关事实由 `packages.json` 与 `fee_rules.json` 提供；承运商与服务等级以 `shipments.json`、`carriers.json` 对齐。也就是说，账单审核首先是字段一致性审核，其次才是金额差异解释。  
D05 样例已经给出典型形态：承运商账单处于待审核状态，系统可按计费重与费规重算，并识别账单差异，最终由财务生成费用异议建议。该样例说明财务审核的核心是“可追溯的结构化证据链”，不是人工口头判断贵不贵。

## 触发条件
- 用户输入 `waybill_no` 与 `carrier_bill_amount`，请求审核承运商账单。
- `settlement_bills.json` 中同运单账单状态为待审核，或财务人工标记存在差异。
- 需要解释账单为什么与系统重算结果不一致。
- 需要生成 `freight_bill_difference` 类工单或财务异议建议。
- 运单与账单均有效，且非取消、非无主单据。

## 需要查询的数据
- `settlement_bills.json`：确认 `bill_no`、`waybill_no`、`carrier_code`、`carrier_bill_amount`、`bill_status`。
- `packages.json`：确认 `actual_weight_kg`、`chargeable_weight_kg`、尺寸、`is_remote_area`、`value_added_services`。
- `fee_rules.json`：确认首重、续重、体积重除数、偏远附加、超时扣罚等计费规则是否存在。
- `shipments.json`：确认承运商、服务等级与账单是否一致。
- `carriers.json`：确认服务等级口径，辅助校验账单归属。
- `exception_tickets.json`：确认是否已有费用差异复核工单。
- 建议工具：`settlement_calculate_freight`、`settlement_get_fee_breakdown`、`settlement_audit_carrier_bill`、`ticket_create_exception_ticket`。

## 判断逻辑
- 第一步，先校验账单主数据是否一致：账单中的运单号、承运商编码必须能与运单事实对应起来。
- 第二步，再校验计费基础。账单审核应以 `packages.json` 的计费重、尺寸和偏远标记为基础，不以客服描述或 PDF 截图作为真源。
- 第三步，系统重算必须来自 Settlement 工具读取 `fee_rules.json` 后的结果。RAG 只解释“为何要按计费重、偏远附加、增值服务逐项核验”。
- 第四步，发现差异时，应优先从以下方向解释：账单是否按错误服务等级计费、是否忽略计费重口径、是否重复计入偏远或增值服务、是否遗漏已存在的异常结算调整。
- 第五步，若账单状态仍为待审核，则输出“可发起异议/复核”；若账单已确认，则输出“可申请追溯复核”，不宣称系统已自动更正。
- 第六步，若同单还存在超时扣罚、赔付审核等结算事项，需分开记录，不将不同结算项直接相抵后写入单条规则结论。

## 责任归因
- 账单差异复核主责为 `finance`。
- 若差异源自承运商、服务等级、运单信息挂错，可同步归因给 `logistics` 协助核对承运关系。
- 结构化计费资料缺失、账单与运单不匹配、规则版本不清时，归入 `manual_review`。
- 客服通常不参与账单审核结论，只在必要时说明内部对账中。

## 处理建议
- 先做主数据一致性校验，再做费用重算，避免把错单问题误判成单纯价格问题。
- 审核输出应包含“账单金额来源”“系统重算来源”“差异可能成因”“是否建议建复核工单”四部分。
- 对存在差异的账单，建议直接生成 `freight_bill_difference` 工单，并关联原账单号、运单号和重算摘要。
- 若差异来自计费重或增值服务，需把对应包裹字段一并写入工单，便于财务与承运商对账。
- 不在规则正文中写具体金额重算结果；金额展示应来自工具输出或后续系统界面。

## 升级条件
- `settlement_bills.json` 与 `shipments.json` 的承运商或运单映射不一致。
- `packages.json` 缺少计费关键字段，导致系统无法稳定重算。
- 账单已确认，但差异明显，需要发起追溯异议。
- 一张账单同时涉及超时扣罚、赔付冲抵等多类结算事项，需人工拆分核对。
- 已存在开放中的费用差异工单，但新的重算结果与旧工单记录冲突。

## 客服表达建议
- 本规则通常不直接面向客户输出。
- 如必须对客说明，可统一表述为：相关费用正在内部复核中，不影响我们继续推进异常处理。
- 不建议向客户披露承运商账单结构、内部费规细节或对账争议过程。
- 不建议把账单差异与客户赔付承诺直接绑定。

## 工单字段建议
- `scenario_code`：`freight_bill_audit`
- `exception_type`：`freight_bill_difference`
- `responsible_department`：`finance`
- `ticket_type`：`freight_audit_ticket`
- 关键审核字段：`bill_no`、`waybill_no`、`carrier_code`、`carrier_bill_amount`、`bill_status`
- 计费依据字段：`chargeable_weight_kg`、`actual_weight_kg`、`is_remote_area`、`value_added_services`
- 复核字段：系统重算摘要、差异原因分类、是否已通知物流协查、是否需承运商对账异议
