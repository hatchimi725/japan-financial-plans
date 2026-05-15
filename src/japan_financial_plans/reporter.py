"""収集・処理済みデータからHTMLレポートを生成するモジュール。"""

from __future__ import annotations

import html
import logging
from datetime import datetime
from pathlib import Path

from .models import PlanInfo, ProcessedResult

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"

RISK_COLOR = {"低": "#22c55e", "中": "#f59e0b", "高": "#ef4444", "なし": "#94a3b8"}
RISK_LABEL = {"低": "低リスク", "中": "中リスク", "高": "高リスク", "なし": "リスクなし"}

_CSS = """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Hiragino Sans", "Yu Gothic UI", sans-serif;
  background: #f8fafc;
  color: #1e293b;
  line-height: 1.7;
}
.site-header {
  background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
  color: #fff;
  padding: 2rem 2.5rem 1.5rem;
}
.site-header h1 { font-size: 1.6rem; font-weight: 700; }
.site-header .meta { font-size: 0.8rem; opacity: 0.75; margin-top: 0.3rem; }
.container { max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }
.plan-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
  padding: 1.8rem 2rem;
  margin-bottom: 2rem;
}
.plan-card h2 {
  font-size: 1.25rem;
  font-weight: 700;
  border-left: 4px solid #2563eb;
  padding-left: 0.75rem;
  margin-bottom: 1rem;
}
.summary {
  background: #eff6ff;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  margin-bottom: 1.2rem;
  color: #1e40af;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.8rem;
  margin-bottom: 1.4rem;
}
.info-item {
  background: #f1f5f9;
  border-radius: 8px;
  padding: 0.7rem 1rem;
}
.info-item .label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: #64748b;
  margin-bottom: 0.25rem;
}
.info-item .value { font-size: 0.92rem; font-weight: 500; }
.risk-badge {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
}
.section-title {
  font-size: 0.88rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: #475569;
  margin: 1.2rem 0 0.5rem;
}
ul.points, ol.steps {
  padding-left: 1.4rem;
  font-size: 0.93rem;
}
ul.points li, ol.steps li { margin-bottom: 0.3rem; }
.sources { margin-top: 0.4rem; }
.sources a {
  display: block;
  font-size: 0.82rem;
  color: #2563eb;
  word-break: break-all;
  margin-bottom: 0.2rem;
  text-decoration: none;
}
.sources a:hover { text-decoration: underline; }
/* index page */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1.2rem;
  margin-bottom: 2.5rem;
}
.cat-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0,0,0,.07);
  padding: 1.2rem 1.4rem;
  text-decoration: none;
  color: inherit;
  transition: box-shadow .15s;
}
.cat-card:hover { box-shadow: 0 4px 14px rgba(37,99,235,.18); }
.cat-card .cat-name {
  font-weight: 700;
  font-size: 1rem;
  color: #1e3a5f;
  margin-bottom: 0.4rem;
}
.cat-card .cat-summary { font-size: 0.83rem; color: #64748b; }
table.compare {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0,0,0,.07);
}
table.compare th {
  background: #1e3a5f;
  color: #fff;
  padding: 0.65rem 1rem;
  text-align: left;
  font-weight: 600;
}
table.compare td { padding: 0.6rem 1rem; border-bottom: 1px solid #e2e8f0; }
table.compare tr:last-child td { border-bottom: none; }
table.compare tr:hover td { background: #eff6ff; }
h2.section { font-size: 1.1rem; font-weight: 700; margin: 2rem 0 1rem; color: #1e3a5f; }
"""


def _slug(name: str) -> str:
    return name.replace(" ", "_").replace("/", "-").replace("（", "").replace("）", "")


def _page(title: str, body: str, back_link: bool = False) -> str:
    back = '<p style="margin-bottom:1rem"><a href="./INDEX.html" style="color:#2563eb;font-size:.9rem">← 一覧に戻る</a></p>' if back_link else ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<header class="site-header">
  <h1>{html.escape(title)}</h1>
  <p class="meta">自動生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</header>
<div class="container">
{back}
{body}
</div>
</body>
</html>"""


def _render_plan_html(plan: PlanInfo) -> str:
    risk_color = RISK_COLOR.get(plan.risk_level, "#94a3b8")
    risk_label = RISK_LABEL.get(plan.risk_level, plan.risk_level)

    key_points_html = "".join(f"<li>{html.escape(p)}</li>" for p in plan.key_points)
    action_steps_html = "".join(f"<li>{html.escape(s)}</li>" for s in plan.action_steps)
    sources_html = "".join(
        f'<a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(u)}</a>'
        for u in plan.source_urls[:5]
    )

    return f"""<div class="plan-card">
  <h2>{html.escape(plan.name)}</h2>
  <div class="summary">{html.escape(plan.summary)}</div>
  <div class="info-grid">
    <div class="info-item">
      <div class="label">加入資格</div>
      <div class="value">{html.escape(plan.eligibility)}</div>
    </div>
    <div class="info-item">
      <div class="label">年間上限額</div>
      <div class="value">{html.escape(plan.annual_limit)}</div>
    </div>
    <div class="info-item">
      <div class="label">税制優遇</div>
      <div class="value">{html.escape(plan.tax_benefit)}</div>
    </div>
    <div class="info-item">
      <div class="label">リスク</div>
      <div class="value">
        <span class="risk-badge" style="background:{risk_color}">{html.escape(risk_label)}</span>
      </div>
    </div>
  </div>
  <div class="section-title">ポイント</div>
  <ul class="points">{key_points_html}</ul>
  <div class="section-title">始め方</div>
  <ol class="steps">{action_steps_html}</ol>
  <div class="section-title">参考リンク</div>
  <div class="sources">{sources_html}</div>
</div>"""


def generate_category_report(result: ProcessedResult) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    body = "\n".join(_render_plan_html(plan) for plan in result.plans)
    html_content = _page(result.category, body, back_link=True)

    path = REPORTS_DIR / f"{_slug(result.category)}.html"
    path.write_text(html_content, encoding="utf-8")
    logger.info("レポート生成: %s", path.name)
    return path


def generate_index(results: list[ProcessedResult]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    sorted_results = sorted(results, key=lambda r: r.category)

    cards_html = ""
    for result in sorted_results:
        plan = result.plans[0] if result.plans else None
        summary = html.escape(plan.summary if plan else "情報なし")
        cards_html += f"""<a class="cat-card" href="./{_slug(result.category)}.html">
  <div class="cat-name">{html.escape(result.category)}</div>
  <div class="cat-summary">{summary}</div>
</a>\n"""

    rows_html = ""
    for result in sorted_results:
        for plan in result.plans:
            risk_color = RISK_COLOR.get(plan.risk_level, "#94a3b8")
            risk_label = RISK_LABEL.get(plan.risk_level, plan.risk_level)
            rows_html += f"""<tr>
  <td><a href="./{_slug(result.category)}.html" style="color:#2563eb;text-decoration:none">{html.escape(plan.category)}</a></td>
  <td>{html.escape(plan.annual_limit)}</td>
  <td>{html.escape(plan.tax_benefit[:40])}{"..." if len(plan.tax_benefit) > 40 else ""}</td>
  <td><span class="risk-badge" style="background:{risk_color}">{html.escape(risk_label)}</span></td>
</tr>\n"""

    body = f"""<h2 class="section">カテゴリ一覧</h2>
<div class="card-grid">
{cards_html}</div>
<h2 class="section">比較表</h2>
<table class="compare">
  <thead><tr><th>カテゴリ</th><th>上限額</th><th>税制優遇</th><th>リスク</th></tr></thead>
  <tbody>{rows_html}</tbody>
</table>"""

    html_content = _page("日本国内 ファイナンシャルプラン 情報まとめ", body)
    path = REPORTS_DIR / "INDEX.html"
    path.write_text(html_content, encoding="utf-8")
    logger.info("インデックス生成: %s", path.name)
    return path
