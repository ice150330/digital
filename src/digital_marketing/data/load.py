"""加载原始营销 CSV（只读真相源）。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from digital_marketing.data.import_csv import EXPECTED_COLUMNS, validate_columns


def load_raw_csv(path: Path | str) -> pd.DataFrame:
    """读取 CSV 并校验表头；不修改源文件。"""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"原始 CSV 不存在: {path}")
    df = pd.read_csv(path)
    validate_columns(df)
    # 仅保留权威列顺序
    return df[EXPECTED_COLUMNS].copy()
