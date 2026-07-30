"""Stacking 集成：LGBM + RF + Logistic → meta LogisticRegression（内部 5-fold OOF）。

红线：stacking 内部 CV 仅作用于传入的 train 矩阵；valid/test 用法与其他实验一致。
"""

from __future__ import annotations

import logging

from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)


def build_stacking(*, seed: int, class_weight: str | None = "balanced", cv: int = 5) -> StackingClassifier:
    """构造 stacking 分类器；LightGBM 不可用则降级为 RF+ExtraTrees+LR。"""
    estimators: list[tuple[str, object]] = []
    try:
        import lightgbm as lgb

        estimators.append(
            (
                "lgbm",
                lgb.LGBMClassifier(
                    n_estimators=200,
                    learning_rate=0.05,
                    num_leaves=31,
                    class_weight=class_weight,
                    random_state=seed,
                    verbosity=-1,
                ),
            )
        )
    except Exception as e:  # noqa: BLE001 — 明确降级
        logger.warning("LightGBM 不可用 (%s)，stacking 基学习器降级", e)
        from sklearn.ensemble import ExtraTreesClassifier

        estimators.append(
            (
                "extra_trees",
                ExtraTreesClassifier(
                    n_estimators=200,
                    max_depth=12,
                    class_weight=class_weight,
                    random_state=seed,
                    n_jobs=-1,
                ),
            )
        )
    estimators.append(
        (
            "rf",
            RandomForestClassifier(
                n_estimators=200,
                max_depth=12,
                class_weight=class_weight,
                random_state=seed,
                n_jobs=-1,
            ),
        )
    )
    estimators.append(
        (
            "lr",
            LogisticRegression(
                max_iter=2000,
                class_weight=class_weight,
                random_state=seed,
            ),
        )
    )
    return StackingClassifier(
        estimators=estimators,
        final_estimator=LogisticRegression(max_iter=1000, random_state=seed),
        stack_method="predict_proba",
        cv=cv,
        passthrough=False,
        n_jobs=None,
    )
