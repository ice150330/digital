---
Topic:
    - 商业
,    - 科技互联网

Field:
    - 机器学习/预测
,    - 数据挖掘

Ext:
    - .csv

DatasetUsage:
    - 1386056

FolderName:
    - /home/mw/input/mkt5655/
---

## **背景描述**
在数字化时代，企业越来越依赖于精准的数据分析来优化营销策略。本数据集通过整合客户基本信息、营销活动反馈、客户互动行为和历史交易记录，帮助营销人员深入理解消费者行为，从而制定更有效的市场定位和推广计划。

数据集记录了客户与数字营销活动的互动情况。它涵盖了人口统计数据、营销特定指标、客户参与度指标以及历史购买数据，为数字营销领域的预测建模和分析提供了丰富的信息。

![image.png](https://cdn.kesci.com/upload/image/sfxda5obk0.png?imageView2/0/w/640/h/640)


## **数据说明**

| 字段             | 说明                                   |
|------------------------|------------------------------------------|
| CustomerID             | 每个客户的唯一标识符。                     |
| Age                    | 客户的年龄。                             |
| Gender                 | 客户的性别（男性/女性）。                 |
| Income                 | 客户的年收入，以美元计。                 |
| CampaignChannel        | 营销活动传递的渠道：电子邮件(Email)、社交媒体(Social Media)、搜索引擎优化(SEO)、付费点击(PPC)、推荐(Referral)）。 |
| CampaignType           | 营销活动的类型：意识(Awareness)、考虑(Consideration)、转化(Conversion)、留存(Retention)。 |
| AdSpend                | 在营销活动上的花费，以美元计。           |
| ClickThroughRate       | 客户点击营销内容的比率。               |
| ConversionRate         | 点击转化为期望行为（如购买）的比率。   |
| AdvertisingPlatform    | 广告平台：保密。                         |
| AdvertisingTool        | 广告工具：保密。                         |
| WebsiteVisits         | 访问网站的总次数。                       |
| PagesPerVisit         | 每次会话平均访问的页面数。             |
| TimeOnSite            | 每次访问平均在网站上花费的时间（分钟）。 |
| SocialShares           | 营销内容在社交媒体上被分享的次数。     |
| EmailOpens            | 营销电子邮件被打开的次数。               |
| EmailClicks            | 营销电子邮件中链接被点击的次数。         |
| PreviousPurchases      | 客户之前进行的购买次数。               |
| LoyaltyPoints          | 客户累积的忠诚度积分数。               |
| Target Variable        | 目标变量：二元变量，表示客户是否转化（1）或未转化（0）。 |


## **数据来源**
[rabie el kharoua](https://www.kaggle.com/rabieelkharoua): [predict-conversion-in-digital-marketing-dataset](https://www.kaggle.com/datasets/rabieelkharoua/predict-conversion-in-digital-marketing-dataset)

原始版本为 8,000 行、20 列，正类率 87.65%。

## **扩增版本说明（2026-08-10）**

当前 `digital_marketing_campaign_dataset.csv` 为 **200,000 行**的扩增版本，
schema 与原始版本完全一致（20 列、列名与取值域不变），由本仓库
`scripts/gen_dataset.py` 按原始数据的生成机制扩增生成：

- **数据性质：** 扩增数据为**合成数据**（由脚本按分布生成），非真实采集的
  业务数据；原始版本本身亦为 Kaggle 作者标注的合成数据。
- **复现方式：** 随机种子固定（默认 `20260810`），相同参数输出完全可复现。
  重新生成：`python scripts/gen_dataset.py --n 200000`
- **标签生成：** 由 logit 模型生成，系数经数值标定，使各特征判别力
  （Cohen's d）与原始 8000 行一致（偏差 ≤0.056）。
- **正类率：** 由 87.65% 调整为 **31.84%**。原始分布下正类为绝对多数类，
  PR-AUC 被压缩在极窄区间，实验矩阵各变体难以体现差异。
- **消融实验支撑：** `EmailOpens`/`EmailClicks` 保持独立抽样（二者不成包含
  关系，`email_inconsistent` 触发率 21.19%，原始 22.21%）；
  `WebsiteVisits==0` 与深度信号并存（`invalid_web_metrics_flag` 触发率
  1.02%，原始 1.86%）；`ConversionRate` 仍与标签相关但主模型默认排除，
  供 E5 泄漏消融使用。

## **问题描述**
**客户转化预测**：利用数据建立模型，预测客户转化的可能性。
**渠道与活动分析**：评估不同营销渠道和活动类型对客户转化的影响。
**关键因素识别**：分析哪些因素最能促进客户的参与度和转化率。
**广告与策略优化**：基于分析结果，调整广告支出和营销策略，以提升ROI。
