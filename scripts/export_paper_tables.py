#!/usr/bin/env python3
"""从 outputs/metrics 导出论文用表（禁止手抄不一致）。"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from digital_marketing.core.paths import ensure_dir, resolve_under_root


PRIMARY = "pr_auc"
COLS = [
    "run_id",
    "exp_id",
    "model_name",
    "pr_auc",
    "cv_pr_auc_mean",
    "cv_pr_auc_std",
    "pr_auc_ci_low",
    "pr_auc_ci_high",
    "roc_auc",
    "f1",
    "brier",
    "accuracy",
    "threshold",
    "ablation",
]


def _load_leaderboard() -> list[dict]:
    path = resolve_under_root("outputs/metrics/leaderboard.json")
    if not path.is_file():
        raise SystemExit(
            f"缺少 {path}，请先 python scripts/02_train_classify.py 或 run_all"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise SystemExit("leaderboard.json 为空或格式错误")
    return data


def _fmt(v: object, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "是" if v else ""
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def to_markdown(rows: list[dict]) -> str:
    lines = [
        f"# 论文指标表（自动导出）",
        "",
        f"- **导出日期：** {date.today().isoformat()}",
        f"- **主指标：** `{PRIMARY}`（PR-AUC）",
        f"- **数据源：** `outputs/metrics/leaderboard.json`",
        f"- **说明：** Accuracy 仅对照；须并列 Dummy（E0）。禁止手改本表后与产物不一致。",
        "",
        "| " + " | ".join(COLS) + " |",
        "| " + " | ".join(["---"] * len(COLS)) + " |",
    ]
    # 按 pr_auc 降序展示（与常见论文表一致）
    ordered = sorted(
        rows,
        key=lambda r: (r.get(PRIMARY) is not None, float(r.get(PRIMARY) or 0)),
        reverse=True,
    )
    for r in ordered:
        cells = [_fmt(r.get(c)) for c in COLS]
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "## 口径备注",
            "",
            "1. 阈值在 valid 搜索，test 仅评估一次；CV 仅在 train 上 5-fold。",
            "2. 默认部署 run：非 Dummy 非消融中 PR-AUC 最高，近并列偏好树/LightGBM。",
            "3. `cv_pr_auc_mean/std` 为 train 上 5-fold；`pr_auc_ci_low/high` 为 test bootstrap 1000 次 95% CI。",
            "4. `ablation=是` 的 run（E5 含 ConversionRate / E6 去质量 flag）仅作消融对照，不参选默认 run。",
            "5. 复现：`python scripts/run_all.py --with-p1 --full` 后重新执行本脚本。",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c) for c in COLS})


def main() -> int:
    rows = _load_leaderboard()
    reports = ensure_dir(resolve_under_root("docs/reports"))
    metrics_dir = ensure_dir(resolve_under_root("outputs/metrics"))

    md_path = reports / f"{date.today().isoformat()}-论文指标表.md"
    csv_path = metrics_dir / "paper_leaderboard.csv"

    md_path.write_text(to_markdown(rows), encoding="utf-8")
    write_csv(rows, csv_path)

    print(f"rows={len(rows)}")
    print(f"-> {md_path}")
    print(f"-> {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
