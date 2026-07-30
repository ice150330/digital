"""清洗：衍生质量 flag，写出 processed，不覆盖 data/ 原始 CSV。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from digital_marketing.core.paths import ensure_dir


def add_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    """主路径：保留异常行并打 flag。

    - email_inconsistent: EmailClicks > EmailOpens
    - invalid_web_metrics_flag: WebsiteVisits==0 但仍有 PagesPerVisit 或 TimeOnSite 深度信号
    """
    out = df.copy()
    email_opens = pd.to_numeric(out["EmailOpens"], errors="coerce").fillna(0)
    email_clicks = pd.to_numeric(out["EmailClicks"], errors="coerce").fillna(0)
    visits = pd.to_numeric(out["WebsiteVisits"], errors="coerce").fillna(0)
    pages = pd.to_numeric(out["PagesPerVisit"], errors="coerce").fillna(0)
    time_on = pd.to_numeric(out["TimeOnSite"], errors="coerce").fillna(0)

    out["email_inconsistent"] = (email_clicks > email_opens).astype(int)
    out["invalid_web_metrics_flag"] = (
        (visits == 0) & ((pages > 0) | (time_on > 0))
    ).astype(int)
    return out


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """清洗入口：类型规范化 + flag。不删除 CustomerID（可查不可入模）。"""
    out = add_quality_flags(df)
    # 标签保证 0/1
    out["Conversion"] = pd.to_numeric(out["Conversion"], errors="coerce").fillna(0).astype(int)
    return out


def save_clean(
    df: pd.DataFrame,
    processed_dir: Path,
    *,
    basename: str = "clean",
) -> dict[str, Any]:
    """写出 clean.csv 与简要 meta；返回路径信息。"""
    processed_dir = ensure_dir(Path(processed_dir))
    csv_path = processed_dir / f"{basename}.csv"
    meta_path = processed_dir / f"{basename}_meta.json"
    df.to_csv(csv_path, index=False)
    meta = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "positive_rate": float(df["Conversion"].mean()) if "Conversion" in df.columns else None,
        "email_inconsistent_count": int(df["email_inconsistent"].sum())
        if "email_inconsistent" in df.columns
        else 0,
        "invalid_web_metrics_count": int(df["invalid_web_metrics_flag"].sum())
        if "invalid_web_metrics_flag" in df.columns
        else 0,
        "path": str(csv_path),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def load_clean_csv(path: Path | str) -> pd.DataFrame:
    """读取已清洗 CSV。"""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"清洗产物不存在: {path}")
    return pd.read_csv(path)
