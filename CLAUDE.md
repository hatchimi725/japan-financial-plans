# japan-financial-plans

日本国内で実行可能なファイナンシャルプランの情報収集・整理ツール。
Tavily（検索）・Firecrawl（スクレイプ）・Claude API（構造化）を組み合わせて自動運用する。

## アーキテクチャ

```
収集 (collector.py)
  └─ Tavily API: 各カテゴリのクエリで最新情報を検索
  └─ Firecrawl API: 公式サイトをスクレイプ
      ↓
処理 (processor.py)
  └─ Claude API: 生データを PlanInfo 構造体に変換・要約
      ↓
保存 (storage.py)
  └─ data/raw/     生JSON（タイムスタンプ付き）
  └─ data/processed/  カテゴリ別の構造化JSON（上書き）
      ↓
レポート (reporter.py)
  └─ reports/<category>.md  カテゴリ別Markdownレポート
  └─ reports/INDEX.md       全カテゴリの比較表
```

## 対象カテゴリ

- 新NISA / iDeCo / ふるさと納税 / 住宅ローン控除
- 生命保険・医療保険 / 企業型DC / 高配当株・インデックス投資

## 必要な環境変数

| 変数名 | 用途 |
|--------|------|
| `TAVILY_API_KEY` | 検索API |
| `FIRECRAWL_API_KEY` | スクレイプAPI |
| `ANTHROPIC_API_KEY` | Claude構造化処理 |

## セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 実行

```bash
# 全カテゴリを収集・処理・レポート生成
japan-financial-plans

# 特定カテゴリのみ
japan-financial-plans --categories 新NISA iDeCo

# レポートのみ再生成（収集・API呼び出しなし）
japan-financial-plans --report-only

# カテゴリ一覧表示
japan-financial-plans --list
```

## よく使うコマンド

```bash
ruff check .
ruff format .
mypy .
pytest
```

## 規約

- 型ヒント必須、`Any` 禁止
- モジュール名: snake_case / クラス名: PascalCase
