#!/usr/bin/env python3
"""高级解释产物：PDP/ICE 网格落盘（默认 run，test 集口径）。

反事实解释为在线计算（POST /explain/counterfactual），本脚本只落 PDP。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from digital_marketing.core.paths import ensure_dir, resolve_under_root  # noqa: E402
from digital_marketing.explain.pdp import compute_pdp_bundle  # noqa: E402
from digital_marketing.features.schema import load_feature_config  # noqa: E402
from digital_marketing.services import artifacts  # noqa: E402
from digital_marketing.services.artifacts import ArtifactError  # noqa: E402


def _top_numeric_features(run_id: str, k: int = 6) -> list[str]:
    """从全局解释产物取 Top 特征，映射回原始数值列；不足按 features.yaml 顺序补。"""
    cfg = load_feature_config()
    numeric = [c for c in cfg.numeric_features]
    picked: list[str] = []
    try:
        glob = artifacts.get_global_explain(run_id)
        for item in glob.get("top_features") or []:
            name = str(item.get("name", ""))
            if name.startswith("num__"):
                raw = name[len("num__"):]
                if raw in numeric and raw not in picked:
                    picked.append(raw)
            if len(picked) >= k:
                break
    except ArtifactError:
        pass
    for c in numeric:
        if len(picked) >= k:
            break
        if c not in picked:
            picked.append(c)
    return picked[:k]


def main() -> int:
    parser = argparse.ArgumentParser(description="PDP/ICE 落盘")
    parser.add_argument("--run-id", default="", help="默认选 leaderboard 最佳非 Dummy 非消融")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--grid-size", type=int, default=40)
    parser.add_argument("--ice-max", type=int, default=50)
    args = parser.parse_args()

    try:
        run_id = args.run_id or artifacts.pick_default_run_id()
        rt = artifacts.load_runtime(run_id)
    except ArtifactError as e:
        print(f"错误: {e.message}", file=sys.stderr)
        return 1

    test_path = resolve_under_root("outputs/processed/test.csv")
    if not test_path.is_file():
        print("缺少 test.csv，请先 python scripts/01_clean_data.py", file=sys.stderr)
        return 1
    test = pd.read_csv(test_path)
    raw_cols = rt["raw_feature_cols"]

    features = _top_numeric_features(run_id, k=args.top_k)
    print(f"run={run_id} pdp features={features}")
    bundle = compute_pdp_bundle(
        rt["model"],
        rt["transformer"],
        test,
        raw_cols,
        features,
        run_id=run_id,
        grid_size=args.grid_size,
        ice_max=args.ice_max,
    )
    out_dir = ensure_dir(resolve_under_root("outputs/explain"))
    out_path = out_dir / f"pdp_{run_id}.json"
    out_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"pdp -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
