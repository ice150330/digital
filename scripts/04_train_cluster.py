#!/usr/bin/env python
"""训练客户分群（K-Means，特征不含 Conversion）。"""

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
from digital_marketing.segment.train import train_segments


def main() -> int:
    parser = argparse.ArgumentParser(description="K-Means 分群")
    parser.add_argument("--n-clusters", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    clean = resolve_under_root("outputs/processed/clean.csv")
    if not clean.is_file():
        print("缺少 clean.csv，请先 python scripts/01_clean_data.py", file=sys.stderr)
        return 1
    df = pd.read_csv(clean)
    summary = train_segments(df, n_clusters=args.n_clusters, seed=args.seed)
    print(json.dumps({"n_clusters": summary["n_clusters"], "n_samples": summary["n_samples"]}, ensure_ascii=False))
    print("->", resolve_under_root("outputs/segments/summary.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
