"""特征 schema：从 features.yaml 解析，硬过滤泄漏列。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from digital_marketing.core.paths import project_root


# 硬红线：无论 yaml 如何写都必须排除
HARD_EXCLUDE = frozenset({"CustomerID", "Conversion"})


@dataclass
class FeatureConfig:
    target: str = "Conversion"
    never_features: list[str] = field(default_factory=list)
    drop_features: list[str] = field(default_factory=list)
    flag_features: list[str] = field(default_factory=list)
    categorical_features: list[str] = field(default_factory=list)
    numeric_features: list[str] = field(default_factory=list)

    def feature_columns(self) -> list[str]:
        """入模列 = numeric + categorical + flag，去掉 never/drop/硬排除。"""
        ban = set(self.never_features) | set(self.drop_features) | set(HARD_EXCLUDE)
        cols: list[str] = []
        for c in list(self.numeric_features) + list(self.categorical_features) + list(self.flag_features):
            if c not in ban and c not in cols:
                cols.append(c)
        # 二次硬过滤
        return [c for c in cols if c not in HARD_EXCLUDE and c != self.target]


def load_feature_config(path: Path | None = None) -> FeatureConfig:
    path = path or (project_root() / "config" / "features.yaml")
    raw: dict[str, Any] = {}
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    return FeatureConfig(
        target=str(raw.get("target", "Conversion")),
        never_features=list(raw.get("never_features") or []),
        drop_features=list(raw.get("drop_features") or []),
        flag_features=list(raw.get("flag_features") or []),
        categorical_features=list(raw.get("categorical_features") or []),
        numeric_features=list(raw.get("numeric_features") or []),
    )


def assert_no_leakage(columns: list[str]) -> None:
    """断言特征列不含 CustomerID / Conversion。"""
    bad = [c for c in columns if c in HARD_EXCLUDE or c == "CustomerID"]
    if bad:
        raise ValueError(f"特征列含禁止入模字段: {bad}")
