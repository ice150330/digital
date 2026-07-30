---
name: channel-conversion-compare
description: 对比各营销渠道/活动类型的转化率差异，输出结构化事实与口径说明
---

# 渠道转化率对比

## 目标
回答「各 CampaignChannel（或 CampaignType）的转化率有何差异」，全部数字来自工具。

## 编排步骤
1. 调 `conversion_by_dimension`（dimension=CampaignChannel）；若用户问活动类型则 CampaignType。
2. 调 `get_dataset_profile` 补充样本量与正类率背景。
3. 若用户追问「是否显著/可信」，追加 `compare_experiments` 提供模型侧证据。

## 输出要求
- 每个维度值给 n 与 conversion_rate（4 位小数）。
- 明确写：维度间差异为**相关关系**，样本不平衡时提示小样本组谨慎解读。
- 禁止口算任何未在工具结果中出现的数字。
