"""Claude APIを使って生データを構造化情報に変換するモジュール。"""

from __future__ import annotations

import json
import logging

import anthropic

from .config import AppConfig
from .models import PlanInfo, ProcessedResult, RawDocument

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
あなたは日本のファイナンシャルプランの専門家です。
提供された情報を分析し、指定されたJSONスキーマに従って構造化してください。
情報が不明な場合は "情報なし" と記載してください。必ずJSONのみを返してください。
"""

_EXTRACTION_PROMPT = """\
以下は「{category}」に関する収集情報です。
この情報を整理し、以下のJSONスキーマで返してください。

収集情報:
{content}

JSONスキーマ:
{{
  "name": "プラン名（カテゴリ名と同じでよい）",
  "summary": "100字以内の概要",
  "eligibility": "加入・利用資格（年齢・職業・条件）",
  "annual_limit": "年間上限額または掛金上限",
  "tax_benefit": "税制優遇の内容（所得控除・非課税など）",
  "risk_level": "低|中|高|なし のいずれか",
  "key_points": ["重要ポイントを3〜5個の箇条書き"],
  "action_steps": ["今すぐ始めるための具体的手順を3〜5ステップ"],
  "source_urls": ["参照URL一覧"]
}}
"""


def _build_content_block(docs: list[RawDocument]) -> str:
    seen: set[str] = set()
    parts: list[str] = []
    for doc in docs:
        if doc.url in seen:
            continue
        seen.add(doc.url)
        parts.append(f"### {doc.title}\nURL: {doc.url}\n{doc.content[:2000]}")
    return "\n\n---\n\n".join(parts[:10])


def process_category(
    category_name: str,
    docs: list[RawDocument],
    config: AppConfig,
) -> ProcessedResult:
    """収集済みドキュメントをClaude APIで構造化する。"""
    client = anthropic.Anthropic(api_key=config.anthropic_api_key)
    content_block = _build_content_block(docs)

    prompt = _EXTRACTION_PROMPT.format(category=category_name, content=content_block)

    message = client.messages.create(
        model=config.claude_model,
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()
    # JSONブロックのみ抽出
    if "```" in raw_text:
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("JSON解析失敗 [%s]: %s\nRaw: %s", category_name, exc, raw_text[:200])
        data = {
            "name": category_name,
            "summary": "解析エラー",
            "eligibility": "情報なし",
            "annual_limit": "情報なし",
            "tax_benefit": "情報なし",
            "risk_level": "なし",
            "key_points": [],
            "action_steps": [],
            "source_urls": [d.url for d in docs[:3]],
        }

    source_urls = list({d.url for d in docs if d.url})
    data.setdefault("source_urls", source_urls)

    plan = PlanInfo(category=category_name, **data)
    logger.info("処理完了: %s", category_name)
    return ProcessedResult(category=category_name, plans=[plan])
