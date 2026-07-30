# CHANGE.md — 项目变更记录

> **维护方式：** 人工追加（最新在上）。  
> **何时必记：** 功能、修复、约束/设计变更、依赖、计划决策、安全相关。  
> **与 git：** 不强制一条 commit 一条 CHANGE，但有意义改动不得省略；有 commit 时尽量填写哈希。  
> **权威约束：** 详见 `AGENTS.md` §11。

---

## 条目模板（复制使用）

```markdown
## YYYY-MM-DD — 简短标题

- **类型：** feat | fix | docs | refactor | chore | design | security
- **范围：** 模块或路径
- **摘要：** 做了什么
- **原因：** 为什么做
- **影响：** 对用户/开发/答辩/指标的影响
- **破坏性：** 无 | 有（说明迁移方式）
- **关联：** 计划/issue/commit（可选）
- **验证：** 跑过什么 / 未跑什么
```

---

## 变更日志

## 2026-07-30 — 新增 CLAUDE.md

- **类型：** docs
- **范围：** 仓库根目录 `CLAUDE.md`
- **摘要：** 为 Claude Code 会话提供精简入口：文档边界、目标命令、架构、数据/ML/Agent 红线、前端要点、改动纪律；细节指向 AGENTS/DESIGN/计划，不重复全文
- **原因：** `/init` 初始化仓库指引
- **影响：** 后续 Claude Code 实例优先读 CLAUDE.md 再下钻权威文档
- **破坏性：** 无
- **关联：** `AGENTS.md`、`DESIGN.md`
- **验证：** 文件已写入；当前仍无业务实现，命令为「目标形态」

## 2026-07-30 — Pencil 组件参考库 pen/ui.pen

- **类型：** design
- **范围：** `pen/ui.pen`
- **摘要：**
  - 在空 `ui.pen` 中建立**全量分类组件参考库**（非整页业务页面）
  - 设计 Token 对齐 DESIGN.md §5（色板 / 字体 Inter+IBM Plex Mono / 8px 间距 / 圆角）
  - 分类：00 映射表 · 01 Foundations · 02 Buttons · 03 Forms · 04 Tags · 05 Feedback · 06 Navigation Chrome · 07 Data Display · 08 Charts · 09 Agent · 10 Empty/Error · 11 Business · 12 Overlays & Tabs
  - 可复用组件约 84 个（KpiCard、ModelMetricsTable、ShapBarChart、AgentMessageList、ToolTracePanel、RuntimeBadge、EmptyState 等）
  - 含组件 ↔ 前端路径映射表，便于后续 Vue 实现
- **原因：** 用户要求用 Pencil MCP 设计项目可能用到的全量组件资源库，分类且尽量详细
- **影响：** 前端实现可直接对照组件库；不替代 DESIGN 文档约束
- **破坏性：** 无代码；仅新增设计资源
- **关联：** `DESIGN.md` v0.2.0
- **验证：** snapshot_layout 无问题；关键分区截图目视通过

## 2026-07-30 — 文档职责拆分：DESIGN 仅前端，架构/后端归 AGENTS

- **类型：** docs / design
- **范围：** `AGENTS.md`、`DESIGN.md`、本文件
- **摘要：**
  - **`DESIGN.md` 重写为前端专用**（v0.2.0）：技术栈、路由/布局、视觉 token、组件与图表、页面级约束、接口消费约定、空错态文案、联调清单
  - **`AGENTS.md` 升为开发+架构+后端权威**（v0.2）：硬禁止项、分层架构、数据/ML、API/DTO、Agent/项目内 Pi、配置安全测试、ADR
  - 明确冲突优先级与改动同步规则（UI→DESIGN，架构/API→AGENTS，契约字段两边都改）
- **原因：** 用户要求 DESIGN 聚焦前端详细设计约束，后端与架构类放入 AGENTS
- **影响：** 后续实现与 AI 改库按新分工阅读；旧「DESIGN=全栈设计」形态废止
- **破坏性：** 文档结构破坏性（读者路径变更）；无业务代码
- **关联：** 深度计划仍描述全栈，细节以 AGENTS/DESIGN 新分工为准
- **验证：** 两文件已重写落盘

## 2026-07-30 — 新增 AGENTS / DESIGN / CHANGE 三件套

- **类型：** docs
- **范围：** 仓库根目录 `AGENTS.md`、`DESIGN.md`、`CHANGE.md`
- **摘要：**
  - 新增 `AGENTS.md`：面向人类与 AI 代理的**强约束**（目录归位、指标纪律、数据泄漏红线、项目内 Pi 隔离、Agent grounding、git/CHANGE 纪律等）
  - 新增 `DESIGN.md`：完整系统设计（架构分层、数据与实验、API/DTO、Agent 与项目内 Pi、Vue 设计系统、配置/安全/测试/ADR）
  - 新增本文件：约定人工变更日志格式与首条记录
- **原因：** 支撑后续维护与开发；避免实现漂移和 AI 改库时破坏毕设约束
- **影响：** 此后所有有意义改动需读 AGENTS/DESIGN 并追加 CHANGE；实现阶段不得违背硬禁止项
- **破坏性：** 无（当前几乎无业务代码）
- **关联：** `docs/plans/2026-07-30-数字营销转化分析与AI-Copilot-深度计划.md`
- **验证：** 文件已写入仓库根目录；未运行训练/API（尚无实现）

## 2026-07-30 — 深度计划修订：项目内 Pi CLI

- **类型：** design / docs
- **范围：** `docs/plans/2026-07-30-数字营销转化分析与AI-Copilot-深度计划.md`
- **摘要：** Pi 改为由 `scripts/setup_pi_cli.py` 拉取到 `tools/pi-cli/`；禁止使用用户全局 `pi`；仅服务本项目本地
- **原因：** 用户明确要求项目自带 CLI、与本机全局 Pi 解耦
- **影响：** 后续 `PiRuntime`、验收与演示均以项目内路径为准
- **破坏性：** 无代码；设计约束生效
- **关联：** 计划书修订说明
- **验证：** 计划文档已更新

## 2026-07-30 — 深度计划落盘

- **类型：** docs
- **范围：** `docs/plans/`、`docs/reports/`
- **摘要：** 创建毕设第一版深度计划；建立 docs 目录结构
- **原因：** 固化题目、范围分层、架构、Agent/Pi、24 周里程碑与验收标准
- **影响：** 后续实现以该计划为范围基线
- **破坏性：** 无
- **关联：** —
- **验证：** 文档可读

## 2026-07-30 — 仓库初始化与数据就绪

- **类型：** chore
- **范围：** 仓库根、`data/`
- **摘要：** 初始 git 仓库、MIT LICENSE、空 README、Python `.gitignore`；数字营销转化 CSV 与数据说明
- **原因：** 项目起步
- **影响：** 从零工程骨架待建
- **破坏性：** 无
- **关联：** Initial commit
- **验证：** 数据文件存在于 `data/`
