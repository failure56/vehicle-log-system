# コミットメッセージ指示

## フォーマット

Conventional Commits 形式を使用する:

- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメント
- `test:` テスト追加・修正
- `ci:` CI/CD 設定
- `refactor:` リファクタリング
- `chore:` 雑務（依存関係の更新等）

## ルール

- 件名は日本語OK、50文字以内
- 本文（任意）は件名から1行空けて記述
- スコープはコンポーネント名を使用: `ingestion`, `chunking`, `embedding`, `db`, `api`

## 例

```
feat(api): ベクトル類似検索エンドポイントを追加
fix(chunking): 60秒ウィンドウの境界処理を修正
ci: Issue リライトワークフローのパス修正
docs: README にクイックスタート手順を追加
test(api): /search エンドポイントのユニットテスト追加
```
