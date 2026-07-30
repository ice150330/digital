"""分层 train/valid/test 划分；先 split 后 fit。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from digital_marketing.core.paths import ensure_dir


def stratified_three_way_split(
    df: pd.DataFrame,
    *,
    target: str = "Conversion",
    test_size: float = 0.15,
    valid_size: float = 0.15,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """先切 test，再在剩余上切 valid；返回 train/valid/test 与 meta。

    valid_size 为相对「全量」的目标占比近似：在 (1-test) 剩余上取
    valid_size / (1 - test_size)。
    """
    if target not in df.columns:
        raise ValueError(f"缺少标签列: {target}")
    y = df[target]
    rest, test = train_test_split(
        df,
        test_size=test_size,
        random_state=seed,
        stratify=y,
    )
    valid_ratio = valid_size / (1.0 - test_size)
    train, valid = train_test_split(
        rest,
        test_size=valid_ratio,
        random_state=seed,
        stratify=rest[target],
    )
    meta = {
        "seed": seed,
        "test_size": test_size,
        "valid_size": valid_size,
        "n_train": int(len(train)),
        "n_valid": int(len(valid)),
        "n_test": int(len(test)),
        "pos_rate_train": float(train[target].mean()),
        "pos_rate_valid": float(valid[target].mean()),
        "pos_rate_test": float(test[target].mean()),
    }
    return train.reset_index(drop=True), valid.reset_index(drop=True), test.reset_index(drop=True), meta


def save_splits(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    test: pd.DataFrame,
    meta: dict[str, Any],
    processed_dir: Path,
) -> dict[str, Any]:
    """写出 split CSV 与 splits.json。"""
    processed_dir = ensure_dir(Path(processed_dir))
    paths = {
        "train": processed_dir / "train.csv",
        "valid": processed_dir / "valid.csv",
        "test": processed_dir / "test.csv",
    }
    train.to_csv(paths["train"], index=False)
    valid.to_csv(paths["valid"], index=False)
    test.to_csv(paths["test"], index=False)
    meta_out = {
        **meta,
        "paths": {k: str(v) for k, v in paths.items()},
    }
    splits_json = processed_dir / "splits.json"
    splits_json.write_text(json.dumps(meta_out, ensure_ascii=False, indent=2), encoding="utf-8")
    meta_out["splits_json"] = str(splits_json)
    return meta_out
