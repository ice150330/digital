---
name: customer-shap-narrative
description: 为单个客户生成「预测 + SHAP 解释」的中文叙述，严格引用工具数字
---

# 客户 SHAP 叙述

## 目标
给定 CustomerID，输出该客户的转化概率、阈值判定与 Top SHAP 特征的中文解读。

## 编排步骤
1. 从用户消息提取客户 ID，调 `predict_proba`。
2. 调 `explain_customer`（top_k=8）。
3. 可选：调 `assign_cluster` 补充该客户所属分群。

## 输出要求
- 必须展示 proba（4 位小数）、label、threshold、run_id。
- SHAP 正贡献说「推向转化」、负贡献说「拉低转化」，并标注 method。
- 禁止把 SHAP 贡献说成因果（不说「因为 X 所以转化」），只能说「模型认为 X 将该客户的预测推向/拉离转化」。
