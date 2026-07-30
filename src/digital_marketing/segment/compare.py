"""分群增强：多算法 × K 扫描对比、bootstrap 稳定性、规则化画像命名、PCA 投影。

红线：所有聚类拟合均不含 Conversion / CustomerID / ConversionRate；
转化率仅事后统计（沿用 train_segments 口径）。
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    silhouette_score,
)

from digital_marketing.segment.train import build_segment_matrix

# 画像命名用的特征中文映射（无 LLM 依赖，规则化）
FEATURE_ZH = {
    "Age": "年龄",
    "Income": "收入",
    "AdSpend": "广告花费",
    "ClickThroughRate": "点击率",
    "WebsiteVisits": "站内访问",
    "PagesPerVisit": "页均浏览",
    "TimeOnSite": "停留时长",
    "SocialShares": "社交分享",
    "EmailOpens": "邮件打开",
    "EmailClicks": "邮件点击",
    "PreviousPurchases": "历史购买",
    "LoyaltyPoints": "积分",
}


def _fit_labels(algo: str, X: np.ndarray, k: int, seed: int) -> tuple[np.ndarray, Any]:
    if algo == "kmeans":
        model = KMeans(n_clusters=k, random_state=seed, n_init=10)
        return model.fit_predict(X), model
    if algo == "gmm":
        from sklearn.mixture import GaussianMixture

        model = GaussianMixture(n_components=k, random_state=seed, covariance_type="full")
        return model.fit_predict(X), model
    if algo == "agglomerative":
        model = AgglomerativeClustering(n_clusters=k)
        return model.fit_predict(X), model
    raise ValueError(f"未知聚类算法: {algo}")


def compare_algorithms(
    X: np.ndarray,
    *,
    algos: tuple[str, ...] = ("kmeans", "gmm", "agglomerative"),
    k_range: range = range(2, 9),
    seed: int = 42,
) -> list[dict[str, Any]]:
    """多算法 × K 扫描：silhouette / Calinski-Harabasz / GMM BIC。"""
    rows: list[dict[str, Any]] = []
    for algo in algos:
        for k in k_range:
            try:
                labels, model = _fit_labels(algo, X, k, seed)
                row: dict[str, Any] = {
                    "algo": algo,
                    "k": int(k),
                    "silhouette": float(silhouette_score(X, labels)),
                    "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
                }
                if algo == "gmm" and hasattr(model, "bic"):
                    row["bic"] = float(model.bic(X))
                rows.append(row)
            except Exception as e:  # noqa: BLE001 — 单点失败不阻塞全表
                rows.append({"algo": algo, "k": int(k), "error": str(e)})
    return rows


def bootstrap_stability(
    X: np.ndarray,
    *,
    k: int,
    n_boot: int = 20,
    sample_frac: float = 0.8,
    seed: int = 42,
) -> dict[str, Any]:
    """KMeans bootstrap 稳定性：重采样重训与全量标签的 ARI 均值。"""
    rng = np.random.default_rng(seed)
    base = KMeans(n_clusters=k, random_state=seed, n_init=10).fit_predict(X)
    n = X.shape[0]
    aris: list[float] = []
    for b in range(n_boot):
        idx = rng.choice(n, size=int(n * sample_frac), replace=True)
        labels_b = KMeans(n_clusters=k, random_state=seed + b + 1, n_init=10).fit_predict(X[idx])
        aris.append(float(adjusted_rand_score(base[idx], labels_b)))
    arr = np.asarray(aris)
    return {
        "algo": "kmeans",
        "k": int(k),
        "n_boot": int(n_boot),
        "sample_frac": float(sample_frac),
        "ari_mean": float(arr.mean()),
        "ari_std": float(arr.std(ddof=0)),
        "note": "ARI∈[-1,1]，越高越稳定；>0.75 通常视为稳定",
    }


def auto_name_clusters(clusters: list[dict[str, Any]]) -> dict[int, str]:
    """规则化画像命名：各簇 profile_means 相对全量均值的 z-score 取偏高 Top2。"""
    if not clusters:
        return {}
    # 全量均值（按 share 加权）
    keys = [k for k in clusters[0].get("profile_means", {}) if k in FEATURE_ZH]
    if not keys:
        return {}
    overall = {
        c: sum(
            (cl.get("profile_means", {}).get(c) or 0.0) * (cl.get("share") or 0.0)
            for cl in clusters
        )
        for c in keys
    }
    stds: dict[str, float] = {}
    for c in keys:
        vals = np.array([cl.get("profile_means", {}).get(c) or 0.0 for cl in clusters])
        stds[c] = float(vals.std(ddof=0)) or 1.0
    names: dict[int, str] = {}
    for cl in clusters:
        z = {
            c: ((cl.get("profile_means", {}).get(c) or 0.0) - overall[c]) / stds[c]
            for c in keys
        }
        top = sorted(z.items(), key=lambda kv: -kv[1])[:2]
        parts = [f"高{FEATURE_ZH[c]}" if v >= 0 else f"低{FEATURE_ZH[c]}" for c, v in top]
        names[int(cl["cluster_id"])] = "·".join(parts) + "群"
    return names


def pca_projection(
    X: np.ndarray,
    labels: np.ndarray,
    customer_ids: np.ndarray | None = None,
    *,
    max_points: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    """PCA 2D 投影（≤max_points 抽稀）。"""
    n = X.shape[0]
    rng = np.random.default_rng(seed)
    idx = rng.choice(n, size=min(max_points, n), replace=False) if n > max_points else np.arange(n)
    pca = PCA(n_components=2, random_state=seed)
    coords = pca.fit_transform(X[idx])
    points = []
    for j, i in enumerate(idx):
        row = {"x": float(coords[j, 0]), "y": float(coords[j, 1]), "cluster": int(labels[i])}
        if customer_ids is not None:
            row["customer_id"] = int(customer_ids[i])
        points.append(row)
    return {
        "method": "pca",
        "explained_variance": [float(v) for v in pca.explained_variance_ratio_],
        "n_points": len(points),
        "points": points,
    }


def build_compare_report(
    df: pd.DataFrame,
    *,
    kmeans_k: int = 4,
    seed: int = 42,
    clusters: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """汇总：对比表 + 稳定性 + 自动命名 + PCA 投影（基于现有 KMeans k=4 主分群）。

    clusters：summary.json 的簇画像（含 profile_means/share），传入则生成 auto_names。
    """
    X, _ = build_segment_matrix(df, fit=True)
    comparison = compare_algorithms(X, seed=seed)
    stability = bootstrap_stability(X, k=kmeans_k, seed=seed)
    main_labels = KMeans(n_clusters=kmeans_k, random_state=seed, n_init=10).fit_predict(X)
    customer_ids = df["CustomerID"].to_numpy() if "CustomerID" in df.columns else None
    projection = pca_projection(X, main_labels, customer_ids, seed=seed)
    report: dict[str, Any] = {
        "kmeans_k": int(kmeans_k),
        "seed": int(seed),
        "comparison": comparison,
        "stability": stability,
        "projection": projection,
        "label_excluded": True,
        "disclaimer": "分群训练特征不含 Conversion；簇间差异为相关描述，非因果。",
    }
    if clusters:
        report["auto_names"] = {str(k): v for k, v in auto_name_clusters(clusters).items()}
    return report
