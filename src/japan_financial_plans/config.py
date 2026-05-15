"""収集対象の設定・検索クエリ・APIキー管理。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class PlanCategory:
    name: str
    description: str
    queries: list[str]
    seed_urls: list[str] = field(default_factory=list)


CATEGORIES: list[PlanCategory] = [
    PlanCategory(
        name="新NISA",
        description="少額投資非課税制度（2024年から恒久化）",
        queries=[
            "新NISA 2024 つみたて投資枠 成長投資枠 上限",
            "新NISA 口座開設 証券会社 比較",
            "新NISA 非課税保有限度額 運用方法",
        ],
        seed_urls=[
            "https://www.fsa.go.jp/policy/nisa2/index.html",
        ],
    ),
    PlanCategory(
        name="iDeCo",
        description="個人型確定拠出年金",
        queries=[
            "iDeCo 掛金上限 節税 2024",
            "iDeCo 加入資格 会社員 自営業 主婦",
            "iDeCo 運用商品 選び方 おすすめ",
        ],
        seed_urls=[
            "https://www.ideco-koushiki.jp/",
        ],
    ),
    PlanCategory(
        name="ふるさと納税",
        description="地方自治体への寄付と返礼品・税控除の仕組み",
        queries=[
            "ふるさと納税 控除上限額 計算 2024",
            "ふるさと納税 ワンストップ特例 確定申告",
            "ふるさと納税 おすすめ 返礼品 節税効果",
        ],
        seed_urls=[
            "https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/",
        ],
    ),
    PlanCategory(
        name="住宅ローン控除",
        description="住宅ローン残高に応じた所得税・住民税控除",
        queries=[
            "住宅ローン控除 2024 控除率 上限",
            "住宅ローン控除 条件 新築 中古",
            "住宅ローン控除 確定申告 手続き",
        ],
        seed_urls=[
            "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1213.htm",
        ],
    ),
    PlanCategory(
        name="生命保険・医療保険",
        description="保障と貯蓄を兼ねた保険商品",
        queries=[
            "生命保険料控除 2024 節税 上限",
            "医療保険 掛け捨て 終身 比較",
            "就業不能保険 所得補償保険 違い",
        ],
        seed_urls=[],
    ),
    PlanCategory(
        name="確定拠出年金（企業型DC）",
        description="会社が運営する企業型年金（DC）",
        queries=[
            "企業型DC iDeCo 併用 2024",
            "企業型確定拠出年金 マッチング拠出 節税",
        ],
        seed_urls=[],
    ),
    PlanCategory(
        name="高配当株・インデックス投資",
        description="長期積立投資による資産形成",
        queries=[
            "インデックスファンド 積立 S&P500 オルカン 比較",
            "高配当株 日本株 配当金生活 戦略",
            "積立投資 複利効果 シミュレーション",
        ],
        seed_urls=[],
    ),
]

CATEGORY_MAP: dict[str, PlanCategory] = {c.name: c for c in CATEGORIES}


@dataclass(frozen=True)
class AppConfig:
    tavily_api_key: str
    firecrawl_api_key: str
    anthropic_api_key: str
    max_search_results: int = 5
    max_scrape_pages: int = 3
    claude_model: str = "claude-sonnet-4-6"

    @classmethod
    def from_env(cls) -> "AppConfig":
        missing = []
        for var in ("TAVILY_API_KEY", "FIRECRAWL_API_KEY", "ANTHROPIC_API_KEY"):
            if not os.environ.get(var):
                missing.append(var)
        if missing:
            raise EnvironmentError(f"環境変数が未設定: {', '.join(missing)}")
        return cls(
            tavily_api_key=os.environ["TAVILY_API_KEY"],
            firecrawl_api_key=os.environ["FIRECRAWL_API_KEY"],
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        )
