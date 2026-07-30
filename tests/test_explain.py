"""解释模块（不依赖 matplotlib/shap 全局 import）。"""

from __future__ import annotations

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from digital_marketing.explain.global_shap import compute_global_shap
from digital_marketing.explain.local_shap import compute_local_shap


def test_global_linear_proxy() -> None:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(40, 4))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    model = LogisticRegression(max_iter=500).fit(X, y)
    names = [f"f{i}" for i in range(4)]
    out = compute_global_shap(model, X, names, y=y, max_samples=40, top_k=3)
    assert out["top_features"]
    assert out["method"] in {"linear_coef_proxy", "shap_tree", "permutation_importance"}


def test_local_rf_or_fallback() -> None:
    rng = np.random.default_rng(1)
    X = rng.normal(size=(50, 5))
    y = (X[:, 0] > 0).astype(int)
    model = RandomForestClassifier(n_estimators=20, random_state=0).fit(X, y)
    names = [f"f{i}" for i in range(5)]
    local = compute_local_shap(model, X[0], names, top_k=5)
    assert len(local["top_features"]) <= 5
    assert "method" in local


def test_dummy_local_zero_fallback() -> None:
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    y = np.array([1, 1, 0])
    model = DummyClassifier(strategy="most_frequent").fit(X, y)
    local = compute_local_shap(model, X[0], ["a", "b"], top_k=2)
    assert local["top_features"]
