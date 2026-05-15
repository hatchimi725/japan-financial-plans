"""収集した生データをルールベースで構造化するモジュール（外部APIなし）。"""

from __future__ import annotations

import logging
import re

from .models import PlanInfo, ProcessedResult, RawDocument

logger = logging.getLogger(__name__)

# カテゴリごとの静的メタ情報（APIなしで確実に埋まる部分）
_META: dict[str, dict[str, str]] = {
    "新NISA": {
        "eligibility": "日本在住の18歳以上（口座は1人1口座）",
        "annual_limit": "つみたて投資枠120万円 ＋ 成長投資枠240万円（合計360万円/年）、生涯1,800万円",
        "tax_benefit": "運用益・配当が非課税（無期限）",
        "risk_level": "中",
    },
    "iDeCo": {
        "eligibility": "20歳以上65歳未満の国民年金・厚生年金加入者",
        "annual_limit": "会社員：年14.4万〜27.6万円、自営業：年81.6万円",
        "tax_benefit": "掛金全額所得控除、運用益非課税、受取時も控除あり",
        "risk_level": "中",
    },
    "ふるさと納税": {
        "eligibility": "納税義務のある方なら誰でも（収入に応じた控除上限あり）",
        "annual_limit": "控除上限は年収・家族構成による（例：年収500万・独身で約6万円）",
        "tax_benefit": "2,000円の自己負担で残額が所得税・住民税から控除",
        "risk_level": "なし",
    },
    "住宅ローン控除": {
        "eligibility": "住宅ローンを利用して住宅を取得・居住する方",
        "annual_limit": "年末ローン残高の0.7%（最大35万円/年）、最長13年間",
        "tax_benefit": "所得税・住民税から直接控除（還付）",
        "risk_level": "なし",
    },
    "生命保険・医療保険": {
        "eligibility": "制限なし（健康状態・年齢により条件が変わる場合あり）",
        "annual_limit": "生命保険料控除：一般・医療・個人年金それぞれ最大4万円（合計12万円）",
        "tax_benefit": "支払保険料が所得控除（最大12万円）",
        "risk_level": "低",
    },
    "確定拠出年金（企業型DC）": {
        "eligibility": "企業型DCを導入している会社の従業員",
        "annual_limit": "他の企業年金なし：月5.5万円（年66万円）、他の企業年金あり：月2.75万円",
        "tax_benefit": "掛金が給与扱いにならず非課税、運用益も非課税",
        "risk_level": "中",
    },
    "高配当株・インデックス投資": {
        "eligibility": "証券口座を開設できる方なら誰でも（新NISAと併用推奨）",
        "annual_limit": "新NISA枠内なら非課税（成長投資枠240万円/年）",
        "tax_benefit": "新NISA利用で配当・売却益が非課税",
        "risk_level": "中",
    },
}

# よく出る金額・数値パターン
_AMOUNT_RE = re.compile(r"[\d,]+\s*(?:万円|円|%|％|年|ヶ月|か月)")


def _extract_sentences(docs: list[RawDocument], n: int = 8) -> list[str]:
    """ドキュメント群から重複排除した重要文を抽出する。"""
    seen: set[str] = set()
    sentences: list[str] = []
    for doc in docs:
        for line in re.split(r"[。\n]", doc.content):
            line = line.strip()
            if len(line) < 20 or line in seen:
                continue
            seen.add(line)
            sentences.append(line)
            if len(sentences) >= n * 3:
                break
    # 数値を含む文を優先
    with_num = [s for s in sentences if _AMOUNT_RE.search(s)]
    others = [s for s in sentences if not _AMOUNT_RE.search(s)]
    return (with_num + others)[:n]


def _build_key_points(sentences: list[str], meta: dict[str, str]) -> list[str]:
    points = [
        f"年間上限: {meta['annual_limit']}",
        f"税制優遇: {meta['tax_benefit']}",
        f"加入資格: {meta['eligibility']}",
    ]
    for s in sentences[:3]:
        cleaned = re.sub(r"\s+", " ", s)[:80]
        if cleaned not in points:
            points.append(cleaned)
    return points[:6]


_ACTION_STEPS: dict[str, list[str]] = {
    "新NISA": [
        "証券会社（SBI・楽天・マネックス等）でNISA口座を開設",
        "つみたて投資枠でインデックスファンド（全世界株・S&P500等）を月額設定",
        "成長投資枠で個別株・ETFを購入（任意）",
        "年360万円の上限を意識しながら長期保有",
    ],
    "iDeCo": [
        "金融機関（証券会社・銀行）でiDeCo口座を開設（会社員は事業主証明書が必要）",
        "掛金月額を設定（5,000円〜上限内で1,000円単位）",
        "運用商品を選択（インデックスファンド推奨）",
        "年末調整または確定申告で所得控除を申請",
    ],
    "ふるさと納税": [
        "ふるさとチョイス・さとふる等のポータルで控除上限額をシミュレーション",
        "気に入った自治体・返礼品を選んで寄付",
        "ワンストップ特例申請書を5自治体以内に提出（確定申告不要）",
        "翌年の住民税から控除されていることを確認",
    ],
    "住宅ローン控除": [
        "住宅購入・建築時に省エネ基準適合物件であることを確認",
        "入居翌年に確定申告で初回申請（書類：残高証明書・登記事項証明書等）",
        "2年目以降は年末調整で自動適用（給与所得者の場合）",
        "13年間控除が続くため、毎年残高証明書を保管",
    ],
    "生命保険・医療保険": [
        "現在の保障内容と保険料を整理（不要な保険は見直し）",
        "公的保障（健康保険・傷病手当金等）で賄えない部分を確認",
        "掛け捨て医療保険＋就業不能保険を軸に必要保障を設計",
        "年末調整で生命保険料控除を申請（証明書を保険会社から受取）",
    ],
    "確定拠出年金（企業型DC）": [
        "会社のDC制度の有無・掛金上限を人事部で確認",
        "マッチング拠出が可能な場合は活用（会社掛金と同額まで追加拠出）",
        "運用商品をインデックスファンド中心に設定",
        "iDeCoとの併用可否を確認（2022年改正で条件緩和）",
    ],
    "高配当株・インデックス投資": [
        "証券口座（新NISA口座推奨）を開設",
        "毎月一定額を全世界株・S&P500インデックスファンドに積立設定",
        "高配当株は日本株ETF（1489等）や個別株で分散",
        "配当・分配金は再投資して複利効果を最大化",
    ],
}


def process_category(
    category_name: str,
    docs: list[RawDocument],
    config: object,
) -> ProcessedResult:
    """収集済みドキュメントをルールベースで構造化する。"""
    meta = _META.get(category_name, {
        "eligibility": "詳細は公式サイトを確認",
        "annual_limit": "条件により異なる",
        "tax_benefit": "条件により異なる",
        "risk_level": "中",
    })

    sentences = _extract_sentences(docs)
    key_points = _build_key_points(sentences, meta)
    action_steps = _ACTION_STEPS.get(category_name, ["公式サイトで最新情報を確認してください"])

    source_urls = list(dict.fromkeys(d.url for d in docs if d.url))[:8]

    # 収集テキストから概要を組み立て
    first_content = next((d.content for d in docs if d.content), "")
    summary_base = re.sub(r"\s+", " ", first_content).strip()[:80]
    summary = summary_base if summary_base else f"{category_name}に関する情報をまとめました。"

    plan = PlanInfo(
        category=category_name,
        name=category_name,
        summary=summary,
        eligibility=meta["eligibility"],
        annual_limit=meta["annual_limit"],
        tax_benefit=meta["tax_benefit"],
        risk_level=meta["risk_level"],  # type: ignore[arg-type]
        key_points=key_points,
        action_steps=action_steps,
        source_urls=source_urls,
    )
    logger.info("処理完了: %s (%d件のドキュメントから生成)", category_name, len(docs))
    return ProcessedResult(category=category_name, plans=[plan])
