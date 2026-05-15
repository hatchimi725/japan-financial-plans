"""データモデル定義。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RawDocument(BaseModel):
    category: str
    query: str
    url: str
    title: str
    content: str
    collected_at: datetime = Field(default_factory=datetime.now)
    source: Literal["tavily", "firecrawl"]


class PlanInfo(BaseModel):
    """1つのファイナンシャルプランの構造化情報。"""

    category: str
    name: str
    summary: str
    eligibility: str
    annual_limit: str
    tax_benefit: str
    risk_level: Literal["低", "中", "高", "なし"]
    key_points: list[str]
    action_steps: list[str]
    source_urls: list[str]
    last_updated: datetime = Field(default_factory=datetime.now)


class ProcessedResult(BaseModel):
    category: str
    plans: list[PlanInfo]
    processed_at: datetime = Field(default_factory=datetime.now)
