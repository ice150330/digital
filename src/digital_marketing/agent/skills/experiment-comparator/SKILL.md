---
name: experiment-comparator
description: 对比 E0–E8 实验矩阵：主指标、CV/CI、消融与集成结论
---

# 实验对比

## 目标
解读实验矩阵：哪个模型更好、差异是否显著、消融说明什么。

## 编排步骤
1. 调 `compare_experiments` 取全量 leaderboard（含 CV 均值±std、bootstrap CI、消融标记）。
2. 解读顺序：PR-AUC → CI 重叠判断显著性 → ROC-AUC → F1 →（Accuracy 仅对照 + Dummy 并列）。
3. E5（含 ConversionRate）与 E3 对比说明泄漏特征增益有限；E6 说明质量 flag 贡献。

## 输出要求
- CI 重叠时必须说「差异不显著」，禁止宣称「A 优于 B」。
- E5/E6 必须标注「消融实验，不参选默认 run」。
- 校准结论引用 `get_calibration_summary` 的 brier/ECE 前后对比。
