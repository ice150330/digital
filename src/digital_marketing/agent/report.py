"""分析报告生成：编排只读工具 → 模板组装 markdown → 落盘 outputs/reports/。

红线：报告中的数字只来自工具结果（grounding.facts_from_tool 抽取），
模板不做任何口算；相关非因果口径贯穿全文。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from digital_marketing.agent import grounding
from digital_marketing.agent.tools import run_tool
from digital_marketing.core.paths import ensure_dir, resolve_under_root

REPORT_DISCLAIMER = (
    "本报告由系统自动生成，所有数字来自分析产物（outputs/）与只读工具；"
    "相关关系不构成因果，模拟为期望值口径，不构成收益承诺。"
)

# 报告默认编排：段落标题 → 工具调用
DEFAULT_PLAN: list[tuple[str, str, dict[str, Any]]] = [
    ("数据画像与质量", "get_dataset_profile", {}),
    ("数据质量问题", "get_data_quality_issues", {}),
    ("渠道转化率", "conversion_by_dimension", {"dimension": "CampaignChannel"}),
    ("实验矩阵对比", "compare_experiments", {}),
    ("概率校准", "get_calibration_summary", {}),
    ("营销升降表", "get_lift_table", {}),
    ("全局特征解释", "explain_global", {}),
    ("客户分群", "segment_summary", {}),
    ("关联规则", "top_association_rules", {"min_lift": 1.1, "limit": 8}),
    ("预算分配模拟", "simulate_budget", {}),
]


def generate_analysis_report(
    *,
    title: str = "数字营销转化分析报告",
    sections: list[str] | None = None,
) -> dict[str, Any]:
    """执行编排并落盘 markdown；返回 {report_path, digest, tool_trace}。"""
    plan = DEFAULT_PLAN
    if sections:
        wanted = {s.strip() for s in sections if s.strip()}
        plan = [p for p in DEFAULT_PLAN if p[0] in wanted]

    tool_trace: list[dict[str, Any]] = []
    lines: list[str] = [
        f"# {title}",
        "",
        f"- 生成时间：{datetime.now(timezone.utc).isoformat()}",
        f"- {REPORT_DISCLAIMER}",
        "",
    ]
    ok_count = 0
    for heading, tool, kwargs in plan:
        result = run_tool(tool, **kwargs)
        tool_trace.append(
            {
                "tool": tool,
                "args": kwargs,
                "ok": result.get("ok"),
                "error": result.get("error"),
                "section": heading,
            }
        )
        lines.append(f"## {heading}")
        lines.append("")
        if result.get("ok"):
            ok_count += 1
            for fact in grounding.facts_from_tool(tool, result):
                lines.append(f"- {fact}")
        else:
            lines.append(f"- （工具不可用：{result.get('error')}）")
        lines.append("")

    lines.append("## 口径与限制")
    lines.append("")
    lines.append("- 主指标为 PR-AUC；Accuracy 仅对照并并列 Dummy。")
    lines.append("- 阈值在 valid 集搜索，test 集一次评估；CV 仅在 train 内。")
    lines.append("- 分群训练不含 Conversion；关联规则与反事实均为相关/模型行为口径。")
    lines.append("")

    out_dir = ensure_dir(resolve_under_root("outputs/reports"))
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"analysis_{ts}.md"
    path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "report_path": str(path),
        "title": title,
        "n_sections": len(plan),
        "n_sections_ok": ok_count,
        "digest": f"{title}：{ok_count}/{len(plan)} 节生成成功，落盘 {path.name}",
        "tool_trace": tool_trace,
        "disclaimer": REPORT_DISCLAIMER,
    }
