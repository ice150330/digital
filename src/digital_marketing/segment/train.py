"""K-Means 分群：训练特征不含 Conversion。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from digital_marketing.core.paths import ensure_dir, resolve_under_root
from digital_marketing.features.schema import load_feature_config


def build_segment_matrix(
    df: pd.DataFrame,
    *,
    feature_columns: list[str] | None = None,
    fit: bool = True,
    transformer: ColumnTransformer | None = None,
) -> tuple[np.ndarray, ColumnTransformer]:
    """构造分群矩阵；禁止含 Conversion / CustomerID。"""
    cfg = load_feature_config()
    cols = feature_columns or [c for c in cfg.feature_columns() if c in df.columns]
    ban = {"Conversion", "CustomerID", "ConversionRate"}
    cols = [c for c in cols if c not in ban]
    if not cols:
        raise ValueError("分群特征列为空")

    num = [c for c in cols if c in cfg.numeric_features or c in cfg.flag_features]
    cat = [c for c in cols if c in cfg.categorical_features]
    # 其余当数值
    rest = [c for c in cols if c not in num and c not in cat]
    num = num + rest

    if transformer is None:
        transformers = []
        if num:
            transformers.append(
                (
                    "num",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    num,
                )
            )
        if cat:
            transformers.append(
                (
                    "cat",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            (
                                "ohe",
                                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                            ),
                        ]
                    ),
                    cat,
                )
            )
        transformer = ColumnTransformer(transformers, remainder="drop")
        if fit:
            X = transformer.fit_transform(df[cols])
        else:
            raise ValueError("transformer 为空且 fit=False")
    else:
        X = transformer.transform(df[cols])
    return np.asarray(X, dtype=float), transformer


def train_segments(
    df: pd.DataFrame,
    *,
    n_clusters: int = 4,
    seed: int = 42,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """训练 KMeans 并写 summary + model。"""
    out_dir = ensure_dir(out_dir or resolve_under_root("outputs/segments"))
    # 训练不含标签
    work = df.copy()
    if "Conversion" in work.columns:
        y = work["Conversion"].astype(float)
    else:
        y = None

    X, transformer = build_segment_matrix(work, fit=True)
    cfg = load_feature_config()
    cols = [c for c in cfg.feature_columns() if c in work.columns and c not in {"Conversion", "CustomerID"}]

    model = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    labels = model.fit_predict(X)

    clusters: list[dict[str, Any]] = []
    for k in range(n_clusters):
        mask = labels == k
        n = int(mask.sum())
        row: dict[str, Any] = {
            "cluster_id": k,
            "n": n,
            "share": float(n / max(len(labels), 1)),
        }
        if y is not None:
            row["conversion_rate"] = float(y[mask].mean()) if n else None
            row["conversion_note"] = "事后统计，未参与聚类拟合"
        # 简单画像：数值均值
        profile = {}
        for c in cfg.numeric_features:
            if c in work.columns:
                profile[c] = float(work.loc[mask, c].mean()) if n else None
        row["profile_means"] = profile
        clusters.append(row)

    summary = {
        "method": "kmeans",
        "n_clusters": n_clusters,
        "n_samples": int(len(labels)),
        "seed": seed,
        "feature_columns": cols,
        "label_excluded": True,
        "disclaimer": "分群训练特征不含 Conversion；簇转化率为事后统计，非因果。",
        "clusters": clusters,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    joblib.dump(
        {"model": model, "transformer": transformer, "feature_columns": cols},
        out_dir / "model.joblib",
    )
    # 可选：样本分配表
    assign_df = pd.DataFrame({"cluster_id": labels})
    if "CustomerID" in work.columns:
        assign_df.insert(0, "CustomerID", work["CustomerID"].values)
    assign_df.to_csv(out_dir / "assignments.csv", index=False)
    return summary
