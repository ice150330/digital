---
name: report-writer
description: 编排全套只读工具生成分析报告 markdown（数字只来自工具结果）
---

# 报告撰写

## 目标
生成结构化分析报告（数据画像 → 实验 → 解释 → 分群/规则 → 模拟 → 口径限制）。

## 编排步骤
1. 调 `generate_analysis_report`（可传 title 或 sections 子集）。
2. 工具内部已按固定计划编排：profile/quality/channel/experiments/calibration/lift/shap/segments/rules/simulate。
3. 返回 report_path 与各节工具执行状态。

## 输出要求
- 报告数字只来自工具结果；某节工具失败时保留「工具不可用」说明而非编数字。
- 报告尾部固定「口径与限制」节：PR-AUC 主指标、valid/test 协议、相关非因果。
- 向用户回复时给出落盘路径与成功节数摘要。
