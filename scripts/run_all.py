#!/usr/bin/env python3
"""一键：清洗 → 训练 → 全局解释 →（可选）分群/规则。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="分析流水线")
    parser.add_argument("--skip-clean", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-explain", action="store_true")
    parser.add_argument("--with-segments", action="store_true", help="训练 K-Means 分群")
    parser.add_argument("--with-rules", action="store_true", help="挖掘关联规则")
    parser.add_argument("--with-p1", action="store_true", help="同时跑分群+规则")
    parser.add_argument(
        "--full",
        action="store_true",
        help="全量矩阵：06（E0–E8 含消融/Stacking/校准）替代 02，并追加 07 PDP / 08 预算模拟 / 09 分群对比",
    )
    args = parser.parse_args()
    py = sys.executable

    if not args.skip_clean:
        run([py, "scripts/01_clean_data.py"])
    if not args.skip_train:
        run([py, "scripts/06_train_full.py" if args.full else "scripts/02_train_classify.py"])
    if not args.skip_explain:
        run([py, "scripts/03_explain_shap.py"])
        if args.full:
            run([py, "scripts/07_explain_advanced.py"])
    if args.full:
        run([py, "scripts/08_simulate_budget.py"])
    if args.with_p1 or args.with_segments:
        run([py, "scripts/04_train_cluster.py"])
        if args.full:
            run([py, "scripts/09_cluster_compare.py"])
    if args.with_p1 or args.with_rules:
        run([py, "scripts/05_mine_rules.py"])
    print("run_all done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
