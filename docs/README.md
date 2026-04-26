# Docs 导航 / Documentation Guide

## 阅读顺序

1. [Project Brief](./Project%20Brief.md)
2. [Canonical Matrix](./Canonical%20Matrix.md)
3. [Agent Design](./Agent%20Design.md)
4. [MCP Design](./MCP%20Design.md)
5. [Mock Data Design](./Mock%20Data%20Design.md)
6. [RAG Design](./RAG%20Design.md)

---

## 每份文档负责什么

|文档|负责内容|不负责内容|
|---|---|---|
|`Project Brief.md`|项目目标、场景范围、MVP 边界、成功标准|字段真源、工具契约、数据文件结构|
|`Canonical Matrix.md`|统一场景、枚举、字段、工具状态和 cross-doc 校验口径|详细设计说明|
|`Agent Design.md`|智能体职责、共享输入输出、知识库路由、案例调用链|Mock 数据字段设计|
|`MCP Design.md`|工具目录、状态、入参出参、错误码、调用方|业务范围定义|
|`Mock Data Design.md`|Mock Data 文件结构、字段、数据来源、案例数据要求|工具行为说明|
|`RAG Design.md`|知识库拆分、路由策略、规则模板、测试分层|结构化数值来源|

---

## 当前统一口径

- 统一采用 `7 个业务场景 + 5 个 MVP 主演示案例`。
- 客服回复是输出能力，不是独立智能体。
- 工单能力公开表述为“草稿生成与处理跟踪建议”，不是正式闭环。
- `carrier_bill_amount` 是账单金额唯一标准字段。
- `inventory` 统一视为 WMS 域内能力。
- RAG 只做规则解释，不直接产出 SLA 数值、费用或计费重。

---

## 使用建议

阅读或修改任意主文档前，先检查 [Canonical Matrix](./Canonical%20Matrix.md) 中的统一口径，避免再次引入场景名、字段名或工具状态不一致的问题。
