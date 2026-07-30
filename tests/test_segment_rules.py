"""分群与关联规则冒烟。"""

from __future__ import annotations

import pandas as pd
import pytest

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


# ---------------------------------------------------------------------------
# 阶段9 W9b：分群对比 / 稳定性 / 自动命名 / PCA 投影
# ---------------------------------------------------------------------------


def _toy_segment_df(n: int = 60) -> pd.DataFrame:
    import numpy as np

    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "CustomerID": range(n),
            "Age": rng.integers(18, 70, n),
            "Income": rng.integers(20000, 150000, n),
            "AdSpend": rng.uniform(100, 5000, n),
            "ClickThroughRate": rng.uniform(0.01, 0.3, n),
            "WebsiteVisits": rng.integers(0, 50, n),
            "PagesPerVisit": rng.uniform(1, 5, n),
            "TimeOnSite": rng.uniform(0.5, 15, n),
            "SocialShares": rng.integers(0, 30, n),
            "EmailOpens": rng.integers(0, 15, n),
            "EmailClicks": rng.integers(0, 10, n),
            "PreviousPurchases": rng.integers(0, 8, n),
            "LoyaltyPoints": rng.integers(0, 4000, n),
            "Gender": rng.choice(["F", "M"], n),
            "CampaignChannel": rng.choice(["Email", "Social", "PPC"], n),
            "CampaignType": rng.choice(["Awareness", "Conversion", "Retention"], n),
            "email_inconsistent": np.zeros(n, dtype=int),
            "invalid_web_metrics_flag": np.zeros(n, dtype=int),
            "Conversion": rng.choice([0, 1], n, p=[0.12, 0.88]),
        }
    )


def test_auto_name_clusters_uses_zscore_top2():
    from digital_marketing.segment.compare import auto_name_clusters

    clusters = [
        {"cluster_id": 0, "share": 0.5, "profile_means": {"Income": 100000.0, "Age": 55.0}},
        {"cluster_id": 1, "share": 0.5, "profile_means": {"Income": 30000.0, "Age": 22.0}},
    ]
    names = auto_name_clusters(clusters)
    assert set(names) == {0, 1}
    assert "收入" in names[0] or "年龄" in names[0]
    assert names[0].endswith("群")


def test_compare_report_contract():
    from digital_marketing.segment.compare import build_compare_report

    df = _toy_segment_df()
    report = build_compare_report(df, kmeans_k=2, seed=42)
    assert report["label_excluded"] is True
    assert {"comparison", "stability", "projection"} <= set(report)
    algos = {r["algo"] for r in report["comparison"]}
    assert {"kmeans", "gmm", "agglomerative"} <= algos
    ks = {r["k"] for r in report["comparison"] if r["algo"] == "kmeans"}
    assert ks == set(range(2, 9))
    assert -1.0 <= report["stability"]["ari_mean"] <= 1.0
    pts = report["projection"]["points"]
    assert pts and {"x", "y", "cluster"} <= set(pts[0])
    assert "customer_id" in pts[0]
    assert "非因果" in report["disclaimer"]


def test_compare_artifact_on_disk():
    import json

    from digital_marketing.core.paths import resolve_under_root

    path = resolve_under_root("outputs/segments") / "compare.json"
    if not path.is_file():
        pytest.skip("需先运行 scripts/09_cluster_compare.py")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["comparison"] and report["projection"]["points"]
    assert "auto_names" in report  # summary.json 存在时应带自动命名
