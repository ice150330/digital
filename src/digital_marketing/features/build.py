"""特征管道：仅在 train 上 fit，再 transform valid/test。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from digital_marketing.core.paths import ensure_dir
from digital_marketing.features.schema import FeatureConfig, assert_no_leakage, load_feature_config


@dataclass
class FeatureBundle:
    """已 fit 的特征变换与列元信息。"""

    transformer: ColumnTransformer
    feature_names: list[str]
    config: FeatureConfig

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        cols = self.config.feature_columns()
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"推理缺列: {missing}")
        return self.transformer.transform(df[cols])


def _make_transformer(cfg: FeatureConfig) -> ColumnTransformer:
    num_cols = [c for c in cfg.numeric_features if c in cfg.feature_columns()]
    cat_cols = [c for c in cfg.categorical_features if c in cfg.feature_columns()]
    flag_cols = [c for c in cfg.flag_features if c in cfg.feature_columns()]
    # flag 当数值处理
    num_all = num_cols + flag_cols

    transformers = []
    if num_all:
        transformers.append(
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        # 利于 Logistic；树模型对缩放不敏感
                        ("scaler", StandardScaler()),
                    ]
                ),
                num_all,
            )
        )
    if cat_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                cat_cols,
            )
        )
    if not transformers:
        raise ValueError("无可用特征列，请检查 features.yaml")
    return ColumnTransformer(transformers=transformers, remainder="drop")


def fit_feature_bundle(train_df: pd.DataFrame, cfg: FeatureConfig | None = None) -> FeatureBundle:
    """仅在 train 上 fit。"""
    cfg = cfg or load_feature_config()
    cols = cfg.feature_columns()
    assert_no_leakage(cols)
    for c in cols:
        if c not in train_df.columns:
            raise ValueError(f"训练数据缺特征列: {c}")
    tr = _make_transformer(cfg)
    tr.fit(train_df[cols])
    # 展开 one-hot 名
    feature_names = list(tr.get_feature_names_out())
    return FeatureBundle(transformer=tr, feature_names=feature_names, config=cfg)


def save_feature_bundle(bundle: FeatureBundle, processed_dir: Path) -> dict[str, Any]:
    processed_dir = ensure_dir(Path(processed_dir))
    joblib_path = processed_dir / "feature_transformer.joblib"
    schema_path = processed_dir / "feature_schema.json"
    joblib.dump(bundle.transformer, joblib_path)
    schema = {
        "feature_columns_raw": bundle.config.feature_columns(),
        "feature_names_out": bundle.feature_names,
        "target": bundle.config.target,
        "drop_features": bundle.config.drop_features,
        "never_features": bundle.config.never_features,
        "transformer_path": str(joblib_path),
    }
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    return schema
