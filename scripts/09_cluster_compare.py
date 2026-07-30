#!/usr/bin/env python3
"""分群对比增强：多算法 × K 扫描 + bootstrap 稳定性 + 画像自动命名 + PCA 投影。

产物：outputs/segments/compare.json（summary.json 保持不变，向后兼容）。
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

from digital_marketing.core.paths import resolve_under_root  # noqa: E402
from digital_marketing.segment.compare import build_compare_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="分群多算法对比与稳定性")
    parser.add_argument("--k", type=int, default=4, help="主 KMeans 簇数（与 04 保持一致）")
    args = parser.parse_args()

    clean = resolve_under_root("outputs/processed/clean.csv")
    if not clean.is_file():
        print("缺少 clean.csv，请先 python scripts/01_clean_data.py", file=sys.stderr)
        return 1
    df = pd.read_csv(clean)

    seg_dir = resolve_under_root("outputs/segments")
    summary_path = seg_dir / "summary.json"
    clusters = None
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        clusters = summary.get("clusters")
        args.k = int(summary.get("n_clusters") or args.k)
    else:
        print("提示: 尚无 summary.json（可先 python scripts/04_train_cluster.py），auto_names 将缺失")

    print(f"cluster compare: k={args.k} n={len(df)} ...", flush=True)
    report = build_compare_report(df, kmeans_k=args.k, clusters=clusters)
    out_path = seg_dir / "compare.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    stab = report["stability"]
    print(f"compare -> {out_path}")
    print(f"stability: ARI={stab['ari_mean']:.3f}±{stab['ari_std']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
