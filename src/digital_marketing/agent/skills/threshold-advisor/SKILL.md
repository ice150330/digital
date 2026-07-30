---
name: threshold-advisor
description: 基于阈值扫描与成本矩阵给出阈值选择建议（valid 搜/test 评估口径）
---

# 阈值顾问

## 目标
回答「该用什么判定阈值」：结合 F1 最优、成本敏感最优与业务约束。

## 编排步骤
1. 调 `get_model_metrics` 确认当前 run 的 threshold（valid F1 搜得）。
2. 引用阈值扫描产物（`GET /models/threshold-scan` 对应数据，经 `compare_experiments` 或直接读 metrics 的 threshold_scan）。
3. 用户给成本矩阵（FP/FN 代价）时，用 best_by_cost 解释推荐阈值。

## 输出要求
- 明确阈值是在 valid 集搜索、test 集只评估一次。
- 成本口径写清「期望成本 = FP×cost_fp + FN×cost_fn，相对比较」。
- 推荐必须带场景（重召回/重精确/成本约束），不给无场景的唯一答案。
