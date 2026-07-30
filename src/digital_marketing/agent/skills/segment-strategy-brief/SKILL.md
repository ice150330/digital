---
name: segment-strategy-brief
description: 基于分群画像生成各簇策略摘要（相关口径，附稳定性证据）
---

# 分群策略摘要

## 目标
输出各客户簇的画像、事后转化率与差异化触达思路。

## 编排步骤
1. 调 `segment_summary` 取簇画像与事后转化率。
2. 需要稳定性证据时，引用 `outputs/segments/compare.json`（bootstrap ARI）。
3. 对重点簇可调 `top_association_rules` 补充相关模式。

## 输出要求
- 每簇：占比、事后转化率（注明「事后统计，未参与拟合」）、2-3 个显著特征。
- 策略建议用「可优先考虑/可测试」措辞，禁止收益承诺。
- 固定附 disclaimer：相关非因果。
