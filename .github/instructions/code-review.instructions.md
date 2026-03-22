---
description: "Use when reviewing Python code in this project. Checks DuckDB read_only setting, SQL injection via parameter binding, Parquet I/O patterns, DuckDB connection close (with/try-finally), Docker volume path consistency, type hints, FastAPI HTTPException usage."
---
# コードレビュー指示

## チェック観点

- DuckDB 接続が `read_only=True` で開かれているか（書き込み不要時）
- 型ヒントが関数シグネチャに付与されているか
- FastAPI エンドポイントで適切な `HTTPException` を返しているか
- Parquet I/O に `pandas.to_parquet()` / `pd.read_parquet()` を使用しているか
- SQL インジェクションのリスクがないか（パラメータバインド使用）
- docstring が記述されているか
- DuckDB 接続が関数内で適切にクローズされているか（`with` 文または `try/finally`）
- Docker ボリュームマウントのパスがコンテナ内パスと一致しているか

## 出力形式

- 🔴 Critical: セキュリティリスク、データ破損の可能性
- 🟡 Warning: 動作はするが改善すべき点
- 🔵 Info: コード品質・可読性の改善提案

各指摘には該当箇所と修正案を提示すること。
