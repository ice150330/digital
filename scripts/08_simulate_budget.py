#!/usr/bin/env python3
"""预算分配模拟预计算：test 集期望价值曲线 + Top-K 触达名单 CSV。

口径：期望值模拟（概率 × 价值 − 成本），非因果 uplift。
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
from digital_marketing.models.classify import _predict_proba_positive  # noqa: E402
from digital_marketing.services import artifacts  # noqa: E402
from digital_marketing.services.artifacts import ArtifactError  # noqa: E402
from digital_marketing.simulate.budget import (  # noqa: E402
    DEFAULT_COST_PER_CONTACT,
    DEFAULT_VALUE_PER_CONVERSION,
    expected_value_curve,
    reach_list,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="预算分配模拟预计算")
    parser.add_argument("--run-id", default="", help="默认选 leaderboard 最佳非 Dummy 非消融")
    parser.add_argument("--value", type=float, default=DEFAULT_VALUE_PER_CONVERSION, help="单客转化价值")
    parser.add_argument("--cost", type=float, default=DEFAULT_COST_PER_CONTACT, help="单次触达成本")
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
    X = rt["transformer"].transform(test[rt["raw_feature_cols"]])
    proba = _predict_proba_positive(rt["model"], X)

    result = expected_value_curve(
        proba, value_per_conversion=args.value, cost_per_contact=args.cost
    )
    result["run_id"] = run_id
    result["calibrated"] = bool(rt["meta"].get("calibrated"))
    result["note"] = "概率为" + ("校准后" if rt["meta"].get("calibrated") else "原始") + "预测概率"

    out_dir = ensure_dir(resolve_under_root("outputs/simulate"))
    curve_path = out_dir / f"budget_curve_{run_id}.json"
    curve_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"curve -> {curve_path} (recommended_k={result['recommended_k']})")

    k = int(result["recommended_k"])
    if k > 0:
        names = reach_list(
            test,
            proba,
            k=k,
            value_per_conversion=args.value,
            cost_per_contact=args.cost,
        )
        list_path = out_dir / f"reach_list_{run_id}.csv"
        names.to_csv(list_path, index=False)
        print(f"reach_list -> {list_path} (k={k})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
