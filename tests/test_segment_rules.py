"""分群与关联规则冒烟。"""

from __future__ import annotations

import pandas as pd

from digital_marketing.rules.mine import mine_rules
from digital_marketing.segment.train import train_segments


def test_train_segments_excludes_label(tmp_path):
    df = pd.DataFrame(
        {
            "CustomerID": [1, 2, 3, 4, 5, 6],
            "Age": [20, 30, 40, 50, 25, 35],
            "Income": [1, 2, 3, 4, 5, 6],
            "AdSpend": [10, 20, 30, 40, 15, 25],
            "ClickThroughRate": [0.1, 0.2, 0.1, 0.3, 0.2, 0.1],
            "WebsiteVisits": [1, 2, 3, 4, 2, 1],
            "PagesPerVisit": [1.0, 2.0, 1.5, 2.5, 1.2, 1.1],
            "TimeOnSite": [1, 2, 3, 4, 2, 1],
            "SocialShares": [0, 1, 0, 2, 1, 0],
            "EmailOpens": [1, 2, 3, 4, 2, 1],
            "EmailClicks": [0, 1, 1, 2, 1, 0],
            "PreviousPurchases": [0, 1, 2, 1, 0, 1],
            "LoyaltyPoints": [10, 20, 30, 40, 15, 25],
            "Gender": ["F", "M", "F", "M", "F", "M"],
            "CampaignChannel": ["Email", "Social", "Email", "PPC", "Social", "Email"],
            "CampaignType": ["Awareness", "Conversion", "Awareness", "Retention", "Conversion", "Awareness"],
            "email_inconsistent": [0, 0, 0, 0, 0, 0],
            "invalid_web_metrics_flag": [0, 0, 0, 0, 0, 0],
            "Conversion": [1, 0, 1, 1, 0, 1],
        }
    )
    summary = train_segments(df, n_clusters=2, seed=42, out_dir=tmp_path)
    assert summary["label_excluded"] is True
    assert summary["n_clusters"] == 2
    assert (tmp_path / "summary.json").is_file()
    assert "Conversion" not in summary["feature_columns"]


def test_mine_rules_writes(tmp_path):
    df = pd.DataFrame(
        {
            "CampaignChannel": ["Email"] * 20 + ["Social"] * 20,
            "CampaignType": ["Conversion"] * 15 + ["Awareness"] * 25,
            "Gender": ["F"] * 25 + ["M"] * 15,
            "Age": list(range(20, 60)),
            "AdSpend": list(range(40)),
            "EmailOpens": list(range(40)),
            "PreviousPurchases": [0, 1] * 20,
            "Conversion": [1] * 30 + [0] * 10,
        }
    )
    payload = mine_rules(df, min_support=0.05, min_confidence=0.2, min_lift=0.5, top_k=20, out_dir=tmp_path)
    assert "disclaimer" in payload
    assert (tmp_path / "top_rules.json").is_file()
