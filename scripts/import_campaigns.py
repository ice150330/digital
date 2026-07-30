#!/usr/bin/env python3
"""从 data/ 只读 CSV 导入营销主数据到 SQLite。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from digital_marketing.core.config import get_settings  # noqa: E402
from digital_marketing.core.logging import setup_logging  # noqa: E402
from digital_marketing.core.paths import resolve_under_root  # noqa: E402
from digital_marketing.data.db import get_session_factory, init_db  # noqa: E402
from digital_marketing.data.import_csv import import_campaigns_from_csv  # noqa: E402


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser(description="导入营销活动 CSV → SQLite")
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="CSV 路径（默认 config 中 raw_csv）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=True,
        help="全量重建 campaigns（默认开启）",
    )
    parser.add_argument(
        "--no-force",
        action="store_true",
        help="不清空已有 campaigns（可能因唯一键失败）",
    )
    args = parser.parse_args()

    settings = get_settings()
    init_db(settings)

    csv_path = resolve_under_root(args.csv) if args.csv else settings.raw_csv
    force = not args.no_force

    factory = get_session_factory(settings)
    with factory() as session:
        batch = import_campaigns_from_csv(session, csv_path, force=force)

    print(
        f"导入完成: rows={batch.row_count} sha256={batch.file_sha256[:16]}… "
        f"source={batch.source_path}"
    )
    print(f"数据库: {settings.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
