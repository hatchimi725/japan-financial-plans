# japan-financial-plans

## 技術スタック

- **言語**: Python 3.11+
- **Linter/Formatter**: ruff
- **型チェック**: mypy (strict)
- **テスト**: pytest

## 規約

- 型ヒント必須（`def func(x: int) -> str:`）
- `Any` 型の使用禁止
- モジュール・ファイル名は snake_case: `data_processor.py`
- クラス名は PascalCase: `DataProcessor`

## セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e ".[dev]"
```

## よく使うコマンド

```bash
ruff check .          # Lint
ruff format .         # Format
mypy .                # 型チェック
pytest                # テスト実行
```
