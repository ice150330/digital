---
name: budget-planner
description: 预算分配模拟：按期望价值排序的触达计划（期望值口径，非因果）
---

# 预算规划

## 目标
给定预算/单客价值/触达成本，输出触达人数建议与期望收益曲线解读。

## 编排步骤
1. 调 `simulate_budget`（可带 budget/value_per_conversion/cost_per_contact）。
2. 解读 recommended_k 与推荐点的 expected_conversions / expected_net。
3. 可配合 `get_lift_table` 说明「高十分位捕获率」与排序价值。

## 输出要求
- 全程「期望值」措辞：期望转化数、期望净收益。
- 必须附 disclaimer：基于历史 test 集预测排序，非因果 uplift、非收益承诺。
- 参数缺失时用默认值并显式说明（value=10、cost=4，盈亏平衡 proba=0.4）。
