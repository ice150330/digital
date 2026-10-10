#!/usr/bin/env python3
"""按基准数据的生成机制做同分布扩增，产出大体量营销转化数据集。

用途：基准 CSV 仅 8000 行，正类率 87.65%，样本量与类别分布都不足以支撑
E0–E8 实验矩阵的对比。本脚本在**完全一致的 schema 与生成机制**下扩增行数，
使清洗层、E5/E6 消融、交叉矩阵、规则挖掘、预算模拟器等既有研究方向不变。

关键还原点（均来自基准数据实测，改动会破坏消融实验）：

- ``EmailOpens``(0-19) 与 ``EmailClicks``(0-9) **独立均匀抽样**，二者不成
  包含关系 —— 这正是 ``email_inconsistent`` 质量 flag 的来源（约 22%）。
  若强制 EmailClicks <= EmailOpens，E6 消融将失去可消融对象。
- ``WebsiteVisits``(0-49) 与 ``PagesPerVisit``/``TimeOnSite`` 独立抽样 ——
  这是 ``invalid_web_metrics_flag`` 的来源（约 2%）。
- ``ConversionRate`` 与标签存在真实相关，但主模型默认排除、仅由 E5 引入，
  E5 因此构成"含泄漏列"的对照实验。
- ``AdvertisingPlatform`` / ``AdvertisingTool`` 为常数列，按原样保留，
  由特征层按"常数丢弃"规则处理。

标签由上述特征经 logit 模型生成，系数经数值标定，使各特征的判别力
（Cohen's d）与基准数据一致。

仅依赖标准库；种子固定，输出可完全复现。
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = PROJECT_ROOT / "data" / "digital_marketing_campaign_dataset.csv"
DEFAULT_N = 200_000
DEFAULT_SEED = 20260810
DEFAULT_POSITIVE_RATE = 0.32

COLUMNS = [
    "CustomerID",
    "Age",
    "Gender",
    "Income",
    "CampaignChannel",
    "CampaignType",
    "AdSpend",
    "ClickThroughRate",
    "ConversionRate",
    "WebsiteVisits",
    "PagesPerVisit",
    "TimeOnSite",
    "SocialShares",
    "EmailOpens",
    "EmailClicks",
    "PreviousPurchases",
    "LoyaltyPoints",
    "AdvertisingPlatform",
    "AdvertisingTool",
    "Conversion",
]

GENDERS = ["Female", "Male"]
CHANNELS = ["Email", "Social Media", "SEO", "PPC", "Referral"]
TYPES = ["Awareness", "Consideration", "Conversion", "Retention"]

# (列名, 低, 高) —— 数值列的取值区间，与基准数据实测范围一致
NUMERIC_RANGES = {
    "Age": (18.0, 69.0),
    "Income": (20000.0, 150000.0),
    "AdSpend": (100.0, 9999.9),
    "ClickThroughRate": (0.01, 0.30),
    "ConversionRate": (0.01, 0.20),
    "WebsiteVisits": (0.0, 49.0),
    "PagesPerVisit": (1.0, 10.0),
    "TimeOnSite": (0.5, 15.0),
    "SocialShares": (0.0, 99.0),
    "EmailOpens": (0.0, 19.0),
    "EmailClicks": (0.0, 9.0),
    "PreviousPurchases": (0.0, 9.0),
    "LoyaltyPoints": (0.0, 4999.0),
}

INT_COLUMNS = {
    "Age",
    "WebsiteVisits",
    "SocialShares",
    "EmailOpens",
    "EmailClicks",
    "PreviousPurchases",
    "LoyaltyPoints",
}

# 数值列的 (均值, 标准差)，用于标准化
MEANS_STD = {
    "Age": (43.63, 14.90),
    "Income": (84664.20, 37578.04),
    "AdSpend": (5000.94, 2837.86),
    "ClickThroughRate": (0.1548, 0.0840),
    "ConversionRate": (0.1044, 0.0550),
    "WebsiteVisits": (24.75, 14.31),
    "PagesPerVisit": (5.549, 2.607),
    "TimeOnSite": (7.728, 4.228),
    "SocialShares": (49.80, 28.90),
    "EmailOpens": (9.477, 5.711),
    "EmailClicks": (4.467, 2.856),
    "PreviousPurchases": (4.486, 2.888),
    "LoyaltyPoints": (2490.27, 1429.44),
}

# 目标判别力（Cohen's d），取自基准数据实测
TARGET_EFFECT = {
    "TimeOnSite": 0.394,
    "EmailClicks": 0.394,
    "EmailOpens": 0.380,
    "AdSpend": 0.379,
    "ClickThroughRate": 0.365,
    "PreviousPurchases": 0.340,
    "PagesPerVisit": 0.313,
    "LoyaltyPoints": 0.289,
    "ConversionRate": 0.283,
    "WebsiteVisits": 0.241,
    "Income": 0.042,
    "SocialShares": -0.035,
    "Age": 0.005,
}

# CampaignType=Conversion 的额外对数几率提升
TARGET_TYPE_BOOST = 0.75

SIGNAL_COLUMNS = [c for c in NUMERIC_RANGES if c in TARGET_EFFECT]

# 基准数据的基准正类率，用于还原 Type 的相对效应
BASE_POSITIVE_RATE = 0.8765
BASE_TYPE_RATE = 0.9336


def sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


def sample_row(rng: random.Random, start_id: int) -> dict[str, object]:
    """抽取一行特征（标签未生成）。"""
    row: dict[str, object] = {}
    row["CustomerID"] = start_id
    for col, (lo, hi) in NUMERIC_RANGES.items():
        v = rng.uniform(lo, hi)
        if col in INT_COLUMNS:
            row[col] = int(round(v))
        else:
            row[col] = v
    row["Gender"] = rng.choice(GENDERS)
    row["CampaignChannel"] = rng.choice(CHANNELS)
    row["CampaignType"] = rng.choice(TYPES)
    row["AdvertisingPlatform"] = "IsConfid"
    row["AdvertisingTool"] = "ToolConfid"
    return row


def logit(p: float) -> float:
    p = min(max(p, 1e-9), 1 - 1e-9)
    return math.log(p / (1 - p))


def build_coefficients(calib_n: int, seed: int, positive_rate: float) -> tuple[dict[str, float], float, float]:
    """数值标定系数，使判别力与基准数据一致且正类率达标。"""
    rng = random.Random(seed)
    betas = {c: TARGET_EFFECT[c] for c in SIGNAL_COLUMNS}
    intercept = logit(positive_rate)
    type_boost = TARGET_TYPE_BOOST

    for _ in range(14):
        ys: list[int] = []
        types: list[str] = []
        vals: dict[str, list[float]] = {c: [] for c in SIGNAL_COLUMNS}
        for i in range(calib_n):
            row = sample_row(rng, 1000 + i)
            z = intercept
            for c in SIGNAL_COLUMNS:
                m, s = MEANS_STD[c]
                xs = (float(row[c]) - m) / s
                z += betas[c] * xs
                vals[c].append(xs)
            if row["CampaignType"] == "Conversion":
                z += type_boost
            y = 1 if rng.random() < sigmoid(z) else 0
            ys.append(y)
            types.append(str(row["CampaignType"]))

        n1 = sum(ys)
        if n1 == 0 or n1 == calib_n:
            intercept += logit(positive_rate) - logit(n1 / calib_n)
            continue
        rate = n1 / calib_n
        # 先把总体正类率拉回目标，再调各特征强度
        intercept += logit(positive_rate) - logit(rate)

        updated = False
        for c in SIGNAL_COLUMNS:
            xs = vals[c]
            mx = sum(xs) / calib_n
            sd = math.sqrt(sum((x - mx) ** 2 for x in xs) / calib_n)
            if sd < 1e-9:
                continue
            xs1 = [xs[i] for i in range(calib_n) if ys[i] == 1]
            xs0 = [xs[i] for i in range(calib_n) if ys[i] == 0]
            m1 = sum(xs1) / n1
            m0 = sum(xs0) / (calib_n - n1)
            d = (m1 - m0) / sd
            target = TARGET_EFFECT[c]
            if abs(d) > 1e-6:
                betas[c] *= target / d
                updated = True

        # Type 相对效应：向基准数据中 Conversion 型相对全量的优势靠拢
        type_idx = [i for i in range(calib_n) if types[i] == "Conversion"]
        if type_idx:
            type_rate = sum(ys[i] for i in type_idx) / len(type_idx)
            # 基准数据中该类相对整体的正类率之比
            ratio_target = BASE_TYPE_RATE / BASE_POSITIVE_RATE
            cur = type_rate / max(rate, 1e-9)
            type_boost += logit(min(max(cur * ratio_target, 1e-6), 1 - 1e-6)) - logit(
                min(max(cur, 1e-6), 1 - 1e-6)
            )
        if not updated:
            break

    return betas, intercept, type_boost


def generate(n: int, seed: int, positive_rate: float) -> list[dict[str, object]]:
    """生成 n 行；系数经小样本标定后用于正式抽样。"""
    betas, intercept, type_boost = build_coefficients(20_000, seed, positive_rate)
    rng = random.Random(seed)
    out: list[dict[str, object]] = []
    base_id = 1_000_000

    for i in range(n):
        row = sample_row(rng, base_id + i)
        z = intercept
        for c in SIGNAL_COLUMNS:
            m, s = MEANS_STD[c]
            z += betas[c] * (float(row[c]) - m) / s
        if row["CampaignType"] == "Conversion":
            z += type_boost
        row["Conversion"] = 1 if rng.random() < sigmoid(z) else 0
        out.append(row)
    return out


def fmt(col: str, value: object) -> str:
    if col in INT_COLUMNS or col in ("CustomerID", "Conversion"):
        return str(int(value))  # type: ignore[arg-type]
    if col in NUMERIC_RANGES:
        return repr(float(value))  # type: ignore[arg-type]
    return str(value)


def write_csv(rows: list[dict[str, object]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow([fmt(c, row[c]) for c in COLUMNS])


def main() -> int:
    ap = argparse.ArgumentParser(description="扩增数字营销转化数据集")
    ap.add_argument("--n", type=int, default=DEFAULT_N, help="生成行数")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help="随机种子")
    ap.add_argument("--positive-rate", type=float, default=DEFAULT_POSITIVE_RATE,
                    help="目标正类率（可辩护区间建议 0.25-0.40）")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="输出 CSV 路径")
    args = ap.parse_args()

    if args.n < 1000:
        print("--n 至少 1000", file=sys.stderr)
        return 2
    if not 0.05 <= args.positive_rate <= 0.95:
        print("--positive-rate 需在 0.05-0.95 之间", file=sys.stderr)
        return 2

    rows = generate(args.n, args.seed, args.positive_rate)
    write_csv(rows, args.out)
    pos = sum(int(r["Conversion"]) for r in rows)
    print(f"已生成 {len(rows)} 行 -> {args.out}")
    print(f"正类率 = {pos / len(rows):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
