import json
import os
import sys
import urllib.request

# Validate required environment variables
token = os.environ.get("GITHUB_TOKEN")
pr_title = os.environ.get("PR_TITLE", "")
pr_body = os.environ.get("PR_BODY", "")

if not token:
    print("Error: GITHUB_TOKEN environment variable is not set", file=sys.stderr)
    sys.exit(1)

# Check if we have at least title or body (after stripping whitespace)
if not pr_title.strip() and not pr_body.strip():
    print("Error: At least one of PR_TITLE or PR_BODY must contain non-whitespace content", file=sys.stderr)
    sys.exit(1)

# Create the prompt for rewriting the PR description
# Handle three cases: 1) title+body, 2) body only, 3) title only
# Note: PR prompt format differs from Issue prompt because PRs focus on
# implementation details (変更内容, テスト, 注意点) while Issues focus on
# requirements (要件, 非要件, 受け入れ条件)
if pr_body.strip():
    # Body exists (with or without title)
    if pr_title.strip():
        pr_content = f"PR題名: {pr_title}\n\nPR説明:\n<<<\n{pr_body}\n>>>"
    else:
        pr_content = f"PR説明:\n<<<\n{pr_body}\n>>>"
else:
    # Only title exists
    pr_content = f"PR題名: {pr_title}\n\n※説明が記載されていないため、題名から内容を類推してください。"

prompt = f"""
以下の GitHub Pull Request の説明をリライトしてください。

{pr_content}
"""

# system プロンプトで出力形式・ルール・制約を明示的に指定
system_prompt = """\
あなたはGitHub Pull Requestの編集者です。
ユーザーから渡されるPRの説明を、レビュアーが理解しやすい形にリライトしてください。

# ルール
- 元の意図や内容を変更しないこと
- 新しい要件は追加しない
- 推測が必要な部分は「未決事項」セクションに分離する
- 断定できないことは断定しない
- 変更内容のサマリを追加する
- 関連するIssueがあれば明記する
- 前置き・後書き・説明文は一切出力しない（Markdownの本文のみ出力すること）

# 出力形式（必ずこの見出し順で出力すること）
## 概要
## 変更内容
## 関連Issue
## テスト
## 注意点
## 未決事項
"""

# GitHub Models API エンドポイント（gpt-4o-mini: Premium 0.25回消費）
url = "https://models.inference.ai.azure.com/chat/completions"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}
data = json.dumps({
    "model": "gpt-4o-mini",
    "messages": [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ],
    "max_tokens": 4096,
    "temperature": 0.3,
}).encode("utf-8")

req = urllib.request.Request(url, data=data, headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if not result.get("choices"):
        print("Error: GitHub Models API returned no response choices", file=sys.stderr)
        sys.exit(1)

    print(result["choices"][0]["message"]["content"])
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print(f"Error calling GitHub Models API ({e.code}): {body}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error calling GitHub Models API: {e}", file=sys.stderr)
    sys.exit(1)
