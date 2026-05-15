"""メインパイプライン: 収集→処理→保存→レポート生成を一括実行。"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .collector import collect_category
from .config import CATEGORIES, CATEGORY_MAP, AppConfig
from .processor import process_category
from .reporter import generate_category_report, generate_index
from .storage import load_all_processed, save_processed, save_raw

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path(__file__).parent.parent.parent.parent / "pipeline.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)


def run(categories: list[str] | None = None, report_only: bool = False) -> None:
    """
    categories: 実行するカテゴリ名リスト。Noneなら全カテゴリ。
    report_only: Trueなら収集・処理をスキップしてレポートのみ再生成。
    """
    config = AppConfig.from_env()
    targets = [CATEGORY_MAP[c] for c in (categories or [])] if categories else CATEGORIES

    if not report_only:
        for cat in targets:
            logger.info("=== [収集] %s ===", cat.name)
            docs = collect_category(cat, config)
            if not docs:
                logger.warning("収集件数0件: %s", cat.name)
                continue
            save_raw(docs, cat.name)

            logger.info("=== [処理] %s ===", cat.name)
            result = process_category(cat.name, docs, config)
            save_processed(result)

            logger.info("=== [レポート] %s ===", cat.name)
            generate_category_report(result)

    logger.info("=== [インデックス生成] ===")
    all_results = load_all_processed()
    index_path = generate_index(all_results)
    logger.info("完了: %s", index_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="日本ファイナンシャルプラン情報収集パイプライン")
    parser.add_argument(
        "--categories",
        nargs="*",
        choices=[c.name for c in CATEGORIES],
        help="実行するカテゴリ（省略時は全カテゴリ）",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="収集・処理をスキップしてレポートのみ再生成",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="対応カテゴリ一覧を表示",
    )
    args = parser.parse_args()

    if args.list:
        for cat in CATEGORIES:
            print(f"  {cat.name}: {cat.description}")
        return

    run(categories=args.categories, report_only=args.report_only)


if __name__ == "__main__":
    main()
