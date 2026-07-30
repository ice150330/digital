"""关联规则挖掘：分箱 + mlxtend（可选）或简易共现回退。"""

from __future__ import annotations

import json
import logging
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from digital_marketing.core.paths import ensure_dir, resolve_under_root

logger = logging.getLogger(__name__)

DISCLAIMER = "关联规则表达相关而非因果，不可直接作为投放因果结论。"


def _bin_frame(df: pd.DataFrame) -> pd.DataFrame:
    """将主要字段分箱为 0/1 事务列。"""
    out = pd.DataFrame(index=df.index)
    if "Conversion" in df.columns:
        out["Conversion=1"] = (pd.to_numeric(df["Conversion"], errors="coerce") == 1).astype(int)
        out["Conversion=0"] = (pd.to_numeric(df["Conversion"], errors="coerce") == 0).astype(int)
    if "CampaignChannel" in df.columns:
        for ch, _ in df["CampaignChannel"].value_counts().head(6).items():
            out[f"Channel={ch}"] = (df["CampaignChannel"] == ch).astype(int)
    if "CampaignType" in df.columns:
        for t, _ in df["CampaignType"].value_counts().head(6).items():
            out[f"Type={t}"] = (df["CampaignType"] == t).astype(int)
    if "Gender" in df.columns:
        for g in df["Gender"].dropna().unique()[:4]:
            out[f"Gender={g}"] = (df["Gender"] == g).astype(int)
    if "Age" in df.columns:
        age = pd.to_numeric(df["Age"], errors="coerce")
        out["Age_high"] = (age >= age.median()).astype(int)
        out["Age_low"] = (age < age.median()).astype(int)
    if "AdSpend" in df.columns:
        sp = pd.to_numeric(df["AdSpend"], errors="coerce")
        out["AdSpend_high"] = (sp >= sp.median()).astype(int)
    if "EmailOpens" in df.columns:
        eo = pd.to_numeric(df["EmailOpens"], errors="coerce")
        out["EmailOpens_high"] = (eo >= eo.median()).astype(int)
    if "PreviousPurchases" in df.columns:
        pp = pd.to_numeric(df["PreviousPurchases"], errors="coerce")
        out["PrevPurchase_high"] = (pp >= max(pp.median(), 1)).astype(int)
    # 去掉全 0/全 1 列
    keep = [c for c in out.columns if 0 < out[c].sum() < len(out)]
    return out[keep]


def _mine_mlxtend(bin_df: pd.DataFrame, min_support: float, min_confidence: float) -> list[dict[str, Any]]:
    from mlxtend.frequent_patterns import apriori, association_rules

    freq = apriori(bin_df.astype(bool), min_support=min_support, use_colnames=True)
    if freq.empty:
        return []
    rules = association_rules(freq, metric="confidence", min_threshold=min_confidence)
    if rules.empty:
        return []
    rows = []
    for _, r in rules.iterrows():
        rows.append(
            {
                "antecedents": " & ".join(sorted(map(str, r["antecedents"]))),
                "consequents": " & ".join(sorted(map(str, r["consequents"]))),
                "support": float(r["support"]),
                "confidence": float(r["confidence"]),
                "lift": float(r["lift"]),
            }
        )
    rows.sort(key=lambda x: x["lift"], reverse=True)
    return rows


def _mine_fallback(bin_df: pd.DataFrame, min_support: float, min_confidence: float) -> list[dict[str, Any]]:
    """无 mlxtend 时：单前件 → 单后件 的 lift 扫描。"""
    n = len(bin_df)
    cols = list(bin_df.columns)
    supports = {c: float(bin_df[c].mean()) for c in cols}
    rows: list[dict[str, Any]] = []
    for a, b in combinations(cols, 2):
        sa, sb = supports[a], supports[b]
        if sa < min_support or sb < min_support:
            continue
        joint = float(((bin_df[a] == 1) & (bin_df[b] == 1)).mean())
        if joint < min_support:
            continue
        conf_ab = joint / sa if sa else 0
        conf_ba = joint / sb if sb else 0
        lift_ab = joint / (sa * sb) if sa * sb else 0
        if conf_ab >= min_confidence:
            rows.append(
                {
                    "antecedents": a,
                    "consequents": b,
                    "support": joint,
                    "confidence": conf_ab,
                    "lift": lift_ab,
                }
            )
        if conf_ba >= min_confidence:
            rows.append(
                {
                    "antecedents": b,
                    "consequents": a,
                    "support": joint,
                    "confidence": conf_ba,
                    "lift": joint / (sa * sb) if sa * sb else 0,
                }
            )
    rows.sort(key=lambda x: x["lift"], reverse=True)
    return rows


def mine_rules(
    df: pd.DataFrame,
    *,
    min_support: float = 0.05,
    min_confidence: float = 0.3,
    min_lift: float = 1.0,
    top_k: int = 50,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out_dir = ensure_dir(out_dir or resolve_under_root("outputs/rules"))
    bin_df = _bin_frame(df)
    method = "pairwise_fallback"
    try:
        rules = _mine_mlxtend(bin_df, min_support, min_confidence)
        method = "mlxtend_apriori"
    except Exception as e:  # noqa: BLE001
        logger.warning("mlxtend 不可用，回退简易规则: %s", e)
        rules = _mine_fallback(bin_df, min_support, min_confidence)

    rules = [r for r in rules if float(r.get("lift") or 0) >= min_lift][:top_k]
    payload = {
        "method": method,
        "min_support": min_support,
        "min_confidence": min_confidence,
        "min_lift": min_lift,
        "n_item_columns": int(bin_df.shape[1]),
        "n_rules": len(rules),
        "disclaimer": DISCLAIMER,
        "rules": rules,
    }
    (out_dir / "top_rules.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload
