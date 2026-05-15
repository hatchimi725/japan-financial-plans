# japan-financial-plans

日本国内で実行可能なファイナンシャルプランの情報収集・整理ツール

## セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 使い方

```bash
python -m japan-financial-plans
```

## 開発

```bash
ruff check .    # Lint
ruff format .   # Format
pytest          # テスト
```
