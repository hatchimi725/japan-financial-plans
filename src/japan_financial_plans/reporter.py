"""収集・処理済みデータからMarkdownレポートを生成するモジュール。"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .models import PlanInfo, ProcessedResult

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"

RISK_EMOJI = {"低": "🟢", "中": "🟡", "高": "🔴", "なし": "⚪"}


def _render_plan(plan: PlanInfo) -> str:
    risk_icon = RISK_EMOJI.get(plan.risk_level, "⚪")
    key_points = "\n".join(f"- {p}" for p in plan.key_points)
    action_steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan.action_steps))
    sources = "\n".join(f"- {u}" for u in plan.source_urls[:5])

    return f"""## {plan.name}

> {plan.summary}

| 項目 | 内容 |
|------|------|
| **加入資格** | {plan.eligibility} |
| **上限額** | {plan.annual_limit} |
| **税制優遇** | {plan.tax_benefit} |
| **リスク** | {risk_icon} {plan.risk_level} |

### ポイント
{key_points}

### 始め方
{action_steps}

### 参考リンク
{sources}
"""


def generate_category_report(result: ProcessedResult) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"# {result.category}", f"*最終更新: {result.processed_at.strftime('%Y-%m-%d %H:%M')}*\n"]
    for plan in result.plans:
        lines.append(_render_plan(plan))

    slug = result.category.replace(" ", "_").replace("/", "-").replace("（", "").replace("）", "")
    path = REPORTS_DIR / f"{slug}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("レポート生成: %s", path.name)
    return path


def generate_index(results: list[ProcessedResult]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 日本国内 ファイナンシャルプラン 情報まとめ",
        f"*自動生成: {now}*\n",
        "## カテゴリ一覧\n",
    ]

    for result in sorted(results, key=lambda r: r.category):
        slug = result.category.replace(" ", "_").replace("/", "-").replace("（", "").replace("）", "")
        plan = result.plans[0] if result.plans else None
        summary = plan.summary if plan else "情報なし"
        lines.append(f"- [{result.category}](./{slug}.md) — {summary}")

    lines += [
        "",
        "---",
        "## 比較表\n",
        "| カテゴリ | 上限額 | 税制優遇 | リスク |",
        "|----------|--------|----------|--------|",
    ]
    for result in sorted(results, key=lambda r: r.category):
        for plan in result.plans:
            risk_icon = RISK_EMOJI.get(plan.risk_level, "⚪")
            lines.append(
                f"| {plan.category} | {plan.annual_limit} | {plan.tax_benefit[:30]}... | {risk_icon} {plan.risk_level} |"
            )

    path = REPORTS_DIR / "INDEX.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("インデックス生成: %s", path.name)
    return path
