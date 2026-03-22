# ドキュメント (Documentation)

Vehicle Log System の技術ドキュメント集です。

## 📚 ドキュメント一覧

### [データフロー図 (data-flow.md)](./data-flow.md)

システム全体のデータ処理フローを図解しています。

**内容:**
- 全体フロー概要（Mermaid 図）
- 各処理ステージの詳細説明
  - Ingestion（データ統合）
  - Chunking（チャンク化）
  - Embedding（ベクトル化）
  - Database（DuckDB）
  - API（FastAPI）
- Docker サービス構成図
- 実行フロー
- トラブルシューティング

**対象読者:**
- システムの全体像を把握したい開発者
- データ処理パイプラインを理解したい方

---

### [システムアーキテクチャ (architecture.md)](./architecture.md)

技術的な設計とコンポーネントの詳細を説明しています。

**内容:**
- システム構成図
- 各コンポーネントの技術スタック
- データベース設計
- API エンドポイント設計
- Docker 構成
- セキュリティ考慮事項
- パフォーマンス最適化
- 拡張性とスケーリング

**対象読者:**
- システムの技術的詳細を知りたい開発者
- アーキテクチャ設計を参考にしたい方
- 本番環境への展開を検討している方

---

## 🚀 クイックスタート

システムの使い方については、[メインREADME](../README.md) を参照してください。

---

## 📊 図の表記について

### Mermaid 図の凡例

ドキュメント内では Mermaid 記法で図を描いています。GitHub 上で自動レンダリングされます。

**色分け:**
- 🔵 青系 (`#e1f5ff`) - 処理サービス
- 🔴 赤系 (`#ffe1e1`) - データベース
- 🟢 緑系 (`#e1ffe1`) - API/インターフェース
- 🟡 黄系 (`#fff4e1`) - データファイル
- ⚪ 灰系 (`#f9f9f9`) - 外部データ

**図の種類:**
- `flowchart` - フローチャート（処理の流れ）
- `graph` - グラフ（構成要素の関係）

---

## 🛠️ ドキュメントの更新

ドキュメントは Markdown 形式で記述されています。

### 編集方法

1. 該当ファイルを編集
2. Mermaid 図の構文を確認（[Mermaid 公式ドキュメント](https://mermaid.js.org/)）
3. GitHub でプレビュー確認
4. コミット・プッシュ

### 推奨事項

- 図は簡潔に保つ
- 日本語と英語を併記（必要に応じて）
- コード例は実際に動作するものを記載
- リンク切れがないか確認

---

## 📝 ドキュメント追加予定

- [ ] API 仕様書（OpenAPI/Swagger）
- [ ] データベーススキーマ詳細
- [ ] デプロイメントガイド
- [ ] 開発者ガイド
- [ ] パフォーマンスベンチマーク結果

---

## 💡 参考リンク

### 外部ドキュメント

- [FastAPI](https://fastapi.tiangolo.com/) - API フレームワーク
- [DuckDB](https://duckdb.org/docs/) - 分析データベース
- [Docker Compose](https://docs.docker.com/compose/) - コンテナオーケストレーション
- [Apache Parquet](https://parquet.apache.org/docs/) - データフォーマット
- [Mermaid](https://mermaid.js.org/) - 図の記法

### リポジトリ内リンク

- [メインREADME](../README.md) - プロジェクト概要
- [docker-compose.yml](../docker-compose.yml) - サービス定義
- [API実装](../api/main.py) - FastAPI コード
- [Chunker実装](../chunking/make_chunks.py) - チャンク化処理

---

## 🤝 貢献

ドキュメントの改善提案や誤字脱字の修正は歓迎します。

1. Issue を作成
2. Pull Request を送信
3. レビュー後にマージ
