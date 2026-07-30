#!/usr/bin/env python3
"""画像原始/清洗数据并可选写出质量报告。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 保证可从仓库根直接运行
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from digital_marketing.core.config import get_settings  # noqa: E402
from digital_marketing.core.paths import ensure_dir, resolve_under_root  # noqa: E402
from digital_marketing.data.clean import clean_dataframe, load_clean_csv  # noqa: E402
from digital_marketing.data.load import load_raw_csv  # noqa: E402
from digital_marketing.data.quality import profile_dataframe, quality_report_markdown  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="数据质量画像")
    parser.add_argument(
        "--from-clean",
        action="store_true",
        help="读取 outputs/processed/clean.csv（否则读原始 CSV 并内存清洗）",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="写入 docs/reports/ 质量报告 Markdown",
    )
    args = parser.parse_args()
    settings = get_settings()

    if args.from_clean:
        clean_path = resolve_under_root("outputs/processed/clean.csv")
        df = load_clean_csv(clean_path)
    else:
        df = clean_dataframe(load_raw_csv(settings.raw_csv))

    profile = profile_dataframe(df)
    out_json = ensure_dir(resolve_under_root("outputs/processed")) / "quality_profile.json"
    out_json.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"n_rows": profile["n_rows"], "positive_rate": profile["positive_rate"], "issues": len(profile["issues"])}, ensure_ascii=False))
    print(f"profile -> {out_json}")

    if args.write_report:
        from datetime import date

        report_dir = ensure_dir(resolve_under_root("docs/reports"))
        report_path = report_dir / f"{date.today().isoformat()}-数据质量报告.md"
        report_path.write_text(
            quality_report_markdown(profile, title="数字营销转化数据集 — 数据质量报告"),
            encoding="utf-8",
        )
        print(f"report -> {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
