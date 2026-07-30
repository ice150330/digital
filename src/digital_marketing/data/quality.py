"""数据质量画像与报告材料。"""

from __future__ import annotations

from typing import Any

import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """生成可序列化质量摘要。"""
    n = len(df)
    missing = {c: int(df[c].isna().sum()) for c in df.columns}
    nunique = {c: int(df[c].nunique(dropna=True)) for c in df.columns}
    constant_cols = [c for c, u in nunique.items() if u <= 1]

    conversion_rate = None
    if "Conversion" in df.columns:
        conversion_rate = float(pd.to_numeric(df["Conversion"], errors="coerce").mean())

    issues: list[dict[str, Any]] = []
    if "email_inconsistent" in df.columns:
        cnt = int(df["email_inconsistent"].sum())
        if cnt:
            issues.append(
                {
                    "code": "email_inconsistent",
                    "count": cnt,
                    "message": "EmailClicks 大于 EmailOpens 的行数",
                }
            )
    if "invalid_web_metrics_flag" in df.columns:
        cnt = int(df["invalid_web_metrics_flag"].sum())
        if cnt:
            issues.append(
                {
                    "code": "invalid_web_metrics",
                    "count": cnt,
                    "message": "WebsiteVisits=0 但仍有深度/时长信号",
                }
            )
    for c in constant_cols:
        issues.append(
            {
                "code": "constant_column",
                "column": c,
                "count": n,
                "message": f"常数列: {c}",
            }
        )

    channel_stats: list[dict[str, Any]] = []
    if "CampaignChannel" in df.columns and "Conversion" in df.columns:
        g = df.groupby("CampaignChannel", dropna=False)["Conversion"]
        for ch, s in g:
            channel_stats.append(
                {
                    "channel": str(ch),
                    "n": int(s.shape[0]),
                    "conversion_rate": float(s.mean()),
                }
            )

    return {
        "n_rows": n,
        "n_columns": len(df.columns),
        "positive_rate": conversion_rate,
        "missing": missing,
        "nunique": nunique,
        "constant_columns": constant_cols,
        "issues": issues,
        "channel_stats": channel_stats,
    }


def quality_report_markdown(profile: dict[str, Any], *, title: str = "数据质量报告") -> str:
    """将 profile 渲染为中文 Markdown。"""
    lines = [
        f"# {title}",
        "",
        f"- 样本量：{profile.get('n_rows')}",
        f"- 列数：{profile.get('n_columns')}",
        f"- 正类占比（Conversion）：{profile.get('positive_rate')}",
        "",
        "## 质量问题",
        "",
    ]
    issues = profile.get("issues") or []
    if not issues:
        lines.append("无显著问题。")
    else:
        for it in issues:
            lines.append(f"- `{it.get('code')}`：{it.get('message')}（count={it.get('count')}）")
    lines.extend(["", "## 渠道转化摘要", ""])
    for ch in profile.get("channel_stats") or []:
        lines.append(
            f"- {ch['channel']}: n={ch['n']}, conversion_rate={ch['conversion_rate']:.4f}"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 原始 CSV 只读；清洗写 `outputs/processed/`。",
            "- `CustomerID` 可查永不入模；`ConversionRate` 主模型默认不含。",
            "- 主实验策略：异常保留 + flag，不做静默删行。",
            "",
        ]
    )
    return "\n".join(lines)
