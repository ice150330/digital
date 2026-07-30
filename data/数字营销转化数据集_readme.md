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

## **问题描述**
**客户转化预测**：利用数据建立模型，预测客户转化的可能性。
**渠道与活动分析**：评估不同营销渠道和活动类型对客户转化的影响。
**关键因素识别**：分析哪些因素最能促进客户的参与度和转化率。
**广告与策略优化**：基于分析结果，调整广告支出和营销策略，以提升ROI。
