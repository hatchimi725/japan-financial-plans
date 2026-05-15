"""データの保存・読み込みを担当するモジュール。"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from .models import ProcessedResult, RawDocument

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def _slug(name: str) -> str:
    return name.replace(" ", "_").replace("/", "-").replace("（", "").replace("）", "")


def save_raw(docs: list[RawDocument], category: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RAW_DIR / f"{_slug(category)}_{ts}.json"
    data = [d.model_dump(mode="json") for d in docs]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("生データ保存: %s (%d件)", path.name, len(docs))
    return path


def save_processed(result: ProcessedResult) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / f"{_slug(result.category)}.json"
    path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("処理済みデータ保存: %s", path.name)
    return path


def load_all_processed() -> list[ProcessedResult]:
    results: list[ProcessedResult] = []
    if not PROCESSED_DIR.exists():
        return results
    for path in sorted(PROCESSED_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append(ProcessedResult.model_validate(data))
        except Exception as exc:
            logger.warning("読み込み失敗 %s: %s", path.name, exc)
    return results
