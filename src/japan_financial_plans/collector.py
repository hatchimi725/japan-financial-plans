"""TavilyとFirecrawlを使って情報を収集するモジュール。"""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from .config import AppConfig, PlanCategory
from .models import RawDocument

logger = logging.getLogger(__name__)


class TavilyCollector:
    BASE_URL = "https://api.tavily.com/search"

    def __init__(self, config: AppConfig) -> None:
        self._key = config.tavily_api_key
        self._max_results = config.max_search_results

    def search(self, query: str, category: str) -> list[RawDocument]:
        payload = {
            "api_key": self._key,
            "query": query,
            "search_depth": "advanced",
            "max_results": self._max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(self.BASE_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

        docs: list[RawDocument] = []
        for result in data.get("results", []):
            docs.append(
                RawDocument(
                    category=category,
                    query=query,
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    collected_at=datetime.now(),
                    source="tavily",
                )
            )
        logger.info("Tavily: %d件取得 [%s]", len(docs), query[:40])
        return docs


class FirecrawlCollector:
    BASE_URL = "https://api.firecrawl.dev/v1/scrape"

    def __init__(self, config: AppConfig) -> None:
        self._key = config.firecrawl_api_key
        self._max_pages = config.max_scrape_pages

    def scrape(self, url: str, category: str) -> RawDocument | None:
        headers = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}
        payload = {"url": url, "formats": ["markdown"]}
        with httpx.Client(timeout=60) as client:
            resp = client.post(self.BASE_URL, json=payload, headers=headers)
            if resp.status_code == 402:
                logger.warning("Firecrawl: クレジット不足 (%s)", url)
                return None
            resp.raise_for_status()
            data = resp.json()

        content = data.get("data", {}).get("markdown", "") or ""
        title = data.get("data", {}).get("metadata", {}).get("title", url)
        logger.info("Firecrawl: スクレイプ完了 [%s]", url[:60])
        return RawDocument(
            category=category,
            query=f"scrape:{url}",
            url=url,
            title=title,
            content=content[:8000],
            collected_at=datetime.now(),
            source="firecrawl",
        )


def collect_category(category: PlanCategory, config: AppConfig) -> list[RawDocument]:
    """1カテゴリ分の情報をTavily検索＋Firecrawlスクレイプで収集する。"""
    docs: list[RawDocument] = []

    tavily = TavilyCollector(config)
    for query in category.queries:
        try:
            docs.extend(tavily.search(query, category.name))
        except Exception as exc:
            logger.error("Tavily エラー [%s]: %s", query, exc)

    firecrawl = FirecrawlCollector(config)
    for url in category.seed_urls[: config.max_scrape_pages]:
        try:
            doc = firecrawl.scrape(url, category.name)
            if doc:
                docs.append(doc)
        except Exception as exc:
            logger.error("Firecrawl エラー [%s]: %s", url, exc)

    return docs
