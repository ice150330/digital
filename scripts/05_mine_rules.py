#!/usr/bin/env python
"""挖掘关联规则（相关非因果）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from digital_marketing.core.paths import resolve_under_root
from digital_marketing.rules.mine import mine_rules


def main() -> int:
    parser = argparse.ArgumentParser(description="关联规则")
    parser.add_argument("--min-support", type=float, default=0.05)
    parser.add_argument("--min-confidence", type=float, default=0.35)
    parser.add_argument("--min-lift", type=float, default=1.05)
    parser.add_argument("--top-k", type=int, default=40)
    args = parser.parse_args()

    clean = resolve_under_root("outputs/processed/clean.csv")
    if not clean.is_file():
        print("缺少 clean.csv，请先 python scripts/01_clean_data.py", file=sys.stderr)
        return 1
    df = pd.read_csv(clean)
    payload = mine_rules(
        df,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift,
        top_k=args.top_k,
    )
    print(
        json.dumps(
            {"method": payload["method"], "n_rules": payload["n_rules"]},
            ensure_ascii=False,
        )
    )
    print("->", resolve_under_root("outputs/rules/top_rules.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
