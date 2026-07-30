#!/usr/bin/env python3
"""清洗原始 CSV → outputs/processed/，并分层 split。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from digital_marketing.core.config import get_settings  # noqa: E402
from digital_marketing.core.paths import ensure_dir, resolve_under_root  # noqa: E402
from digital_marketing.data.clean import clean_dataframe, save_clean  # noqa: E402
from digital_marketing.data.load import load_raw_csv  # noqa: E402
from digital_marketing.data.quality import profile_dataframe, quality_report_markdown  # noqa: E402
from digital_marketing.data.split import save_splits, stratified_three_way_split  # noqa: E402
from digital_marketing.models.classify import load_model_config  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="清洗并划分 train/valid/test")
    parser.add_argument("--no-report", action="store_true", help="不写 docs/reports 质量报告")
    args = parser.parse_args()

    settings = get_settings()
    raw_path = settings.raw_csv
    # 校验源文件存在且我们不会写入它
    if not raw_path.is_file():
        print(f"错误: 原始 CSV 不存在 {raw_path}", file=sys.stderr)
        return 1

    raw_stat = raw_path.stat()
    df = load_raw_csv(raw_path)
    cleaned = clean_dataframe(df)

    processed = ensure_dir(resolve_under_root("outputs/processed"))
    meta = save_clean(cleaned, processed)
    print(f"clean rows={meta['rows']} pos_rate={meta['positive_rate']:.4f}")
    print(f"  email_inconsistent={meta['email_inconsistent_count']} invalid_web={meta['invalid_web_metrics_count']}")

    model_cfg = load_model_config()
    split_cfg = model_cfg.get("split") or {}
    train, valid, test, split_meta = stratified_three_way_split(
        cleaned,
        target="Conversion",
        test_size=float(split_cfg.get("test_size", 0.15)),
        valid_size=float(split_cfg.get("valid_size", 0.15)),
        seed=int(model_cfg.get("seed", settings.seed)),
    )
    split_out = save_splits(train, valid, test, split_meta, processed)
    print(
        f"split train/valid/test = {split_out['n_train']}/{split_out['n_valid']}/{split_out['n_test']}"
    )

    profile = profile_dataframe(cleaned)
    (processed / "quality_profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not args.no_report:
        from datetime import date

        report_dir = ensure_dir(resolve_under_root("docs/reports"))
        report_path = report_dir / f"{date.today().isoformat()}-数据质量报告.md"
        report_path.write_text(
            quality_report_markdown(profile),
            encoding="utf-8",
        )
        print(f"report -> {report_path}")

    # 确认未改动原始 CSV
    raw_stat_after = raw_path.stat()
    if raw_stat.st_mtime_ns != raw_stat_after.st_mtime_ns or raw_stat.st_size != raw_stat_after.st_size:
        print("错误: 原始 CSV 被修改！", file=sys.stderr)
        return 2
    print(f"OK raw CSV untouched: {raw_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
