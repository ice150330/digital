#!/usr/bin/env python3
"""特征 fit（仅 train）+ E0/E1/E3 分类实验 → outputs/models|metrics。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from digital_marketing.core.config import get_settings  # noqa: E402
from digital_marketing.core.paths import resolve_under_root  # noqa: E402
from digital_marketing.features.build import fit_feature_bundle, save_feature_bundle  # noqa: E402
from digital_marketing.features.schema import assert_no_leakage, load_feature_config  # noqa: E402
from digital_marketing.models.classify import (  # noqa: E402
    load_model_config,
    run_experiment,
    write_leaderboard,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="训练分类实验并写 metrics")
    parser.add_argument(
        "--exps",
        default="",
        help="逗号分隔实验 ID，默认跑 model.yaml 全部",
    )
    args = parser.parse_args()

    settings = get_settings()
    processed = resolve_under_root("outputs/processed")
    train_path = processed / "train.csv"
    valid_path = processed / "valid.csv"
    test_path = processed / "test.csv"
    for p in (train_path, valid_path, test_path):
        if not p.is_file():
            print(f"缺少 split 文件，请先: python scripts/01_clean_data.py ({p})", file=sys.stderr)
            return 1

    train = pd.read_csv(train_path)
    valid = pd.read_csv(valid_path)
    test = pd.read_csv(test_path)

    feat_cfg = load_feature_config()
    cols = feat_cfg.feature_columns()
    assert_no_leakage(cols)
    if "ConversionRate" in cols:
        print("错误: ConversionRate 不应进入主模型特征", file=sys.stderr)
        return 2
    if "CustomerID" in cols:
        print("错误: CustomerID 永不入模", file=sys.stderr)
        return 2

    bundle = fit_feature_bundle(train, feat_cfg)
    schema = save_feature_bundle(bundle, processed)
    print(f"features raw={len(cols)} expanded={len(bundle.feature_names)}")

    X_train = bundle.transform(train)
    X_valid = bundle.transform(valid)
    X_test = bundle.transform(test)
    y_train = train[feat_cfg.target].astype(int).to_numpy()
    y_valid = valid[feat_cfg.target].astype(int).to_numpy()
    y_test = test[feat_cfg.target].astype(int).to_numpy()

    model_cfg = load_model_config()
    seed = int(model_cfg.get("seed", settings.seed))
    experiments = list(model_cfg.get("experiments") or [])
    if args.exps.strip():
        want = {x.strip() for x in args.exps.split(",") if x.strip()}
        experiments = [e for e in experiments if str(e.get("id")) in want]

    models_dir = resolve_under_root("outputs/models")
    metrics_dir = resolve_under_root("outputs/metrics")
    rows = []
    for exp in experiments:
        print(f"train {exp.get('id')} {exp.get('name')} ...")
        row = run_experiment(
            exp=exp,
            X_train=X_train,
            y_train=y_train,
            X_valid=X_valid,
            y_valid=y_valid,
            X_test=X_test,
            y_test=y_test,
            seed=seed,
            models_dir=models_dir,
            metrics_dir=metrics_dir,
            feature_schema=schema,
        )
        rows.append(row)
        print(
            f"  pr_auc={row.get('pr_auc'):.4f} roc_auc={row.get('roc_auc')} "
            f"f1={row.get('f1'):.4f} acc={row.get('accuracy'):.4f} thr={row.get('threshold'):.2f}"
        )

    board = write_leaderboard(rows, metrics_dir)
    print(f"leaderboard -> {board}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
