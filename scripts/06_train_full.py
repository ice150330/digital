#!/usr/bin/env python3
"""全量训练矩阵：E0–E8（含消融/Stacking/校准）+ 增强评估落盘。

与 02_train_classify.py 的区别：
- 02 只跑基础实验（快速闭环）
- 本脚本跑 config/model.yaml 全量矩阵；E5/E6 使用特征变体 + per-run transformer；
  E4 缺 imbalanced-learn 时跳过并在 leaderboard 标注 skipped。
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from digital_marketing.core.config import get_settings  # noqa: E402
from digital_marketing.core.paths import resolve_under_root  # noqa: E402
from digital_marketing.features.build import fit_feature_bundle, save_feature_bundle  # noqa: E402
from digital_marketing.features.schema import (  # noqa: E402
    FeatureConfig,
    assert_no_leakage,
    load_feature_config,
)
from digital_marketing.models.classify import (  # noqa: E402
    SmoteUnavailableError,
    load_model_config,
    run_experiment,
    write_leaderboard,
)


def variant_config(cfg: FeatureConfig, variant: str) -> FeatureConfig:
    """构造消融特征变体（不落盘；仅 06 全量矩阵使用）。"""
    if variant == "with_conversion_rate":
        # 泄漏消融：ConversionRate 同时移出 drop 并加入 numeric（yaml 默认不含该列）
        return replace(
            cfg,
            drop_features=[c for c in cfg.drop_features if c != "ConversionRate"],
            numeric_features=[*cfg.numeric_features, "ConversionRate"],
        )
    if variant == "no_quality_flags":
        # 消融：去掉质量 flag
        return replace(cfg, flag_features=[])
    raise ValueError(f"未知特征变体: {variant}")


def variant_schema_dict(bundle, cfg: FeatureConfig) -> dict[str, Any]:
    """变体 run 的 feature_schema 快照（存 meta，不写全局文件）。"""
    return {
        "feature_columns_raw": cfg.feature_columns(),
        "feature_names_out": bundle.feature_names,
        "target": cfg.target,
        "drop_features": cfg.drop_features,
        "never_features": cfg.never_features,
        "variant": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="全量训练矩阵 E0–E8")
    parser.add_argument("--exps", default="", help="逗号分隔实验 ID，默认全部")
    parser.add_argument("--no-cv", action="store_true", help="跳过 5-fold CV（加速试跑）")
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

    # 主特征 bundle（刷新全局产物）
    bundle_main = fit_feature_bundle(train, feat_cfg)
    schema_main = save_feature_bundle(bundle_main, processed)
    print(f"features raw={len(cols)} expanded={len(bundle_main.feature_names)}")

    X_train = bundle_main.transform(train)
    X_valid = bundle_main.transform(valid)
    X_test = bundle_main.transform(test)
    y_train = train[feat_cfg.target].astype(int).to_numpy()
    y_valid = valid[feat_cfg.target].astype(int).to_numpy()
    y_test = test[feat_cfg.target].astype(int).to_numpy()

    model_cfg = load_model_config()
    seed = int(model_cfg.get("seed", settings.seed))
    cost_cfg = model_cfg.get("cost") or {}
    experiments = list(model_cfg.get("experiments") or [])
    if args.exps.strip():
        want = {x.strip() for x in args.exps.split(",") if x.strip()}
        experiments = [e for e in experiments if str(e.get("id")) in want]

    models_dir = resolve_under_root("outputs/models")
    metrics_dir = resolve_under_root("outputs/metrics")
    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    # 变体 bundle 缓存：variant -> (bundle, cfg_v)
    variant_cache: dict[str, tuple[Any, FeatureConfig]] = {}

    for exp in experiments:
        exp_id = str(exp.get("id"))
        name = str(exp.get("name", exp_id))
        variant = exp.get("feature_variant")
        run_id = f"{exp_id}_{name}"
        print(f"train {run_id} ...", flush=True)
        try:
            if variant:
                if variant not in variant_cache:
                    cfg_v = variant_config(feat_cfg, str(variant))
                    assert_no_leakage(cfg_v.feature_columns())
                    bundle_v = fit_feature_bundle(train, cfg_v)
                    variant_cache[variant] = (bundle_v, cfg_v)
                    print(f"  variant {variant}: raw={len(cfg_v.feature_columns())} "
                          f"expanded={len(bundle_v.feature_names)}")
                bundle_v, cfg_v = variant_cache[variant]
                row = run_experiment(
                    exp=exp,
                    X_train=bundle_v.transform(train),
                    y_train=y_train,
                    X_valid=bundle_v.transform(valid),
                    y_valid=y_valid,
                    X_test=bundle_v.transform(test),
                    y_test=y_test,
                    seed=seed,
                    models_dir=models_dir,
                    metrics_dir=metrics_dir,
                    feature_schema=variant_schema_dict(bundle_v, cfg_v),
                    transformer=bundle_v.transformer,
                    enhanced=not args.no_cv,
                    cost_fn=float(cost_cfg.get("fn", 5.0)),
                    cost_fp=float(cost_cfg.get("fp", 1.0)),
                )
            else:
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
                    feature_schema=schema_main,
                    enhanced=not args.no_cv,
                    cost_fn=float(cost_cfg.get("fn", 5.0)),
                    cost_fp=float(cost_cfg.get("fp", 1.0)),
                )
        except SmoteUnavailableError as e:
            print(f"  跳过 {run_id}: {e}")
            skipped.append(
                {
                    "run_id": run_id,
                    "exp_id": exp_id,
                    "model_name": name,
                    "pr_auc": None,
                    "skipped": True,
                    "skip_reason": str(e),
                }
            )
            continue
        rows.append(row)
        cv = row.get("cv") or {}
        print(
            f"  pr_auc={row.get('pr_auc'):.4f} roc_auc={row.get('roc_auc')} "
            f"cv={cv.get('pr_auc_mean', float('nan')):.4f}±{cv.get('pr_auc_std', float('nan')):.4f} "
            f"f1={row.get('f1'):.4f} thr={row.get('threshold'):.2f}",
            flush=True,
        )

    board = write_leaderboard(rows + skipped, metrics_dir)
    print(f"leaderboard -> {board}（{len(rows)} 完成 / {len(skipped)} 跳过）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
