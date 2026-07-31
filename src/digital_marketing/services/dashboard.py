"""大屏 / L1 描述性分析聚合服务（Stage 3）。

口径红线（后端为真相源，前端原样渲染 caliber 字段）：
- 全部为**横截面统计**：campaigns 全表独立计数，非用户路径 cohort；
- 伪漏斗各阶段**不嵌套**，阶段间差异不构成流失率/环比；
- 原始数据无任何业务时间字段，**时序永不可做**。
走主数据轨 SQLite 只读短查询（8k 行毫秒级），不写 outputs 产物文件。
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from digital_marketing.data.db import get_session_factory
from digital_marketing.services.artifacts import ArtifactError

# 维度白名单（防 SQL 注入：仅允许固定列名拼接）
CROSS_DIMS = ("campaign_channel", "campaign_type", "gender")

# 伪漏斗四阶段：横截面独立计数，非嵌套
FUNNEL_STAGES: list[tuple[str, str, str]] = [
    ("clicked", "点击/打开", "email_clicks > 0 OR click_through_rate > 0"),
    ("visited", "到访站点", "website_visits > 0"),
    ("deep_visited", "深度浏览", "website_visits > 0 AND pages_per_visit >= 2"),
    ("converted", "转化", "conversion = 1"),
]

HIST_COLUMNS = ("age", "income", "ad_spend")
HIST_BINS = 10


def _get_db(db: Session | None) -> tuple[Session, bool]:
    if db is not None:
        return db, False
    return get_session_factory()(), True


def _require_campaigns(db: Session) -> int:
    try:
        n = db.execute(text("SELECT COUNT(*) FROM campaigns")).scalar_one()
    except Exception as e:  # noqa: BLE001
        raise ArtifactError(
            "ARTIFACT_MISSING",
            "主数据表未就绪，请先运行 python scripts/init_db.py && python scripts/import_campaigns.py",
        ) from e
    if int(n) == 0:
        raise ArtifactError("ARTIFACT_MISSING", "campaigns 表为空，请先运行 python scripts/import_campaigns.py")
    return int(n)


def get_dashboard(db: Session | None = None) -> dict[str, Any]:
    """KPI 聚合 + 伪漏斗 + 三列直方图（10 等宽箱，lo/hi 可复核）。"""
    sess, owned = _get_db(db)
    try:
        n = _require_campaigns(sess)
        row = sess.execute(
            text(
                """
                SELECT
                    AVG(conversion) AS positive_rate,
                    SUM(ad_spend) AS total_ad_spend,
                    AVG(click_through_rate) AS avg_ctr,
                    AVG(pages_per_visit) AS avg_pages_per_visit,
                    SUM(CASE WHEN previous_purchases > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS repurchase_rate
                FROM campaigns
                """
            )
        ).one()
        kpis = {
            "n_rows": n,
            "positive_rate": _f(row.positive_rate),
            "total_ad_spend": _f(row.total_ad_spend),
            "avg_ctr": _f(row.avg_ctr),
            "avg_pages_per_visit": _f(row.avg_pages_per_visit),
            "repurchase_rate": _f(row.repurchase_rate),
        }

        funnel = []
        for stage, label, cond in FUNNEL_STAGES:
            cnt = sess.execute(text(f"SELECT COUNT(*) FROM campaigns WHERE {cond}")).scalar_one()
            funnel.append(
                {
                    "stage": stage,
                    "label": label,
                    "count": int(cnt),
                    "rate_vs_total": round(int(cnt) / n, 4) if n else 0.0,
                }
            )

        histograms: dict[str, list[dict[str, Any]]] = {}
        for col in HIST_COLUMNS:
            vals = [r[0] for r in sess.execute(text(f"SELECT {col} FROM campaigns")).all()]  # noqa: S608 — col 来自白名单常量
            histograms[col] = _hist_bins(pd.Series(vals, dtype=float).dropna())

        return {
            "kpis": kpis,
            "funnel": funnel,
            "histograms": histograms,
            "caliber": (
                f"横截面统计：campaigns 全表独立计数（n={n}），非用户路径 cohort；"
                "伪漏斗各阶段不嵌套，阶段间差异不构成流失率；数据无业务时间字段，不支持时序。"
            ),
            "source": f"sqlite.campaigns(n={n})",
            "notes": {"time_series_impossible": True, "funnel_is_pseudo": True},
        }
    finally:
        if owned:
            sess.close()


def get_cross_matrix(row_dim: str, col_dim: str, db: Session | None = None) -> dict[str, Any]:
    """二维交叉转化率矩阵（维度白名单校验）。"""
    if row_dim not in CROSS_DIMS or col_dim not in CROSS_DIMS:
        raise ArtifactError(
            "VALIDATION_ERROR",
            f"维度必须是 {list(CROSS_DIMS)} 之一: row_dim={row_dim}, col_dim={col_dim}",
        )
    if row_dim == col_dim:
        raise ArtifactError("VALIDATION_ERROR", "row_dim 与 col_dim 不能相同")
    sess, owned = _get_db(db)
    try:
        n = _require_campaigns(sess)
        rows = sess.execute(
            text(
                f"""
                SELECT {row_dim} AS r, {col_dim} AS c, COUNT(*) AS n, AVG(conversion) AS cr
                FROM campaigns GROUP BY {row_dim}, {col_dim}
                """  # noqa: S608 — 维度经白名单校验
            )
        ).all()
        cells = [
            {"row": str(x.r), "col": str(x.c), "n": int(x.n), "conversion_rate": _f(x.cr)}
            for x in rows
        ]
        rt = sess.execute(
            text(
                f"SELECT {row_dim} AS r, COUNT(*) AS n, AVG(conversion) AS cr FROM campaigns GROUP BY {row_dim}"
            )
        ).all()
        ct = sess.execute(
            text(
                f"SELECT {col_dim} AS c, COUNT(*) AS n, AVG(conversion) AS cr FROM campaigns GROUP BY {col_dim}"
            )
        ).all()
        return {
            "row_dim": row_dim,
            "col_dim": col_dim,
            "cells": cells,
            "row_totals": [{"key": str(x.r), "n": int(x.n), "conversion_rate": _f(x.cr)} for x in rt],
            "col_totals": [{"key": str(x.c), "n": int(x.n), "conversion_rate": _f(x.cr)} for x in ct],
            "caliber": f"横截面交叉统计：按 {row_dim} × {col_dim} 分组（n={n}），组间差异为相关关系。",
        }
    finally:
        if owned:
            sess.close()


def _f(v: Any) -> float:
    return round(float(v), 6) if v is not None else 0.0


def _hist_bins(series: pd.Series) -> list[dict[str, Any]]:
    """10 等宽箱；常数列退化为单箱。"""
    if series.empty:
        return []
    lo, hi = float(series.min()), float(series.max())
    if lo == hi:
        return [{"lo": lo, "hi": hi, "count": int(len(series))}]
    cuts = pd.cut(series, bins=HIST_BINS, include_lowest=True)
    out = []
    counts = cuts.value_counts().sort_index()
    for interval, cnt in counts.items():
        out.append({"lo": round(float(interval.left), 4), "hi": round(float(interval.right), 4), "count": int(cnt)})
    return out
