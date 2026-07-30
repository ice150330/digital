#!/usr/bin/env python3
"""为指定/默认 run 计算全局解释并落盘。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from digital_marketing.core.paths import resolve_under_root  # noqa: E402
from digital_marketing.explain.global_shap import compute_global_shap, save_global_shap  # noqa: E402
from digital_marketing.services import artifacts  # noqa: E402
from digital_marketing.services.artifacts import ArtifactError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="全局 SHAP/贡献落盘")
    parser.add_argument("--run-id", default="", help="默认选 leaderboard 最佳非 Dummy")
    parser.add_argument("--max-samples", type=int, default=200)
    parser.add_argument("--top-k", type=int, default=15)
    args = parser.parse_args()

    try:
        run_id = args.run_id or artifacts.pick_default_run_id()
        rt = artifacts.load_runtime(run_id)
    except ArtifactError as e:
        print(f"错误: {e.message}", file=sys.stderr)
        return 1

    train_path = resolve_under_root("outputs/processed/train.csv")
    if not train_path.is_file():
        print("缺少 train.csv", file=sys.stderr)
        return 1
    train = pd.read_csv(train_path)
    cols = rt["raw_feature_cols"]
    X = rt["transformer"].transform(train[cols])
    y = train["Conversion"].astype(int).to_numpy() if "Conversion" in train.columns else None
    names = rt["feature_names"]

    payload = compute_global_shap(
        rt["model"],
        X,
        names,
        y=y,
        max_samples=args.max_samples,
        top_k=args.top_k,
    )
    payload["run_id"] = run_id
    payload["model_name"] = rt["meta"].get("model_name")
    out = save_global_shap(payload, resolve_under_root("outputs/explain"), run_id)
    print(json.dumps({"run_id": run_id, "method": payload["method"], "path": str(out)}, ensure_ascii=False))
    # 预缓存 2 个样例客户
    samples_dir = resolve_under_root("outputs/explain/samples")
    samples_dir.mkdir(parents=True, exist_ok=True)
    clean = pd.read_csv(resolve_under_root("outputs/processed/clean.csv"))
    # 取 test 中各 1 个
    ids = clean["CustomerID"].head(3).tolist()
    for cid in ids:
        try:
            exp = artifacts.explain_customer(customer_id=int(cid), run_id=run_id, top_k=8)
            p = samples_dir / f"customer_{cid}.json"
            # 去掉不可序列化
            p.write_text(json.dumps(exp, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"sample -> {p}")
        except Exception as e:  # noqa: BLE001
            print(f"sample {cid} skip: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
