import os
import sys
from openai import OpenAI

# Validate required environment variables
api_key = os.environ.get("OPENAI_API_KEY")
pr_title = os.environ.get("PR_TITLE", "")
pr_body = os.environ.get("PR_BODY", "")

if not api_key:
    print("Error: OPENAI_API_KEY environment variable is not set", file=sys.stderr)
    sys.exit(1)

# Check if we have at least title or body (after stripping whitespace)
if not pr_title.strip() and not pr_body.strip():
    print("Error: At least one of PR_TITLE or PR_BODY must contain non-whitespace content", file=sys.stderr)
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

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
以下は人間が手動で作成した GitHub Pull Request の説明です。
内容を変更せず、レビュアーが理解しやすい形にリライトしてください。

ルール:
- 新しい要件は追加しない
- 推測が必要な部分は「未決事項」として分離
- 断定できないことは断定しない
- 変更内容のサマリを追加
- 関連するIssueがあれば明記

出力形式:
## 概要
## 変更内容
## 関連Issue
## テスト
## 注意点
## 未決事項

{pr_content}
"""

try:
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    
    if not res.choices or len(res.choices) == 0:
        print("Error: OpenAI API returned no response choices", file=sys.stderr)
        sys.exit(1)
    
    print(res.choices[0].message.content)
except Exception as e:
    print(f"Error calling OpenAI API: {e}", file=sys.stderr)
    sys.exit(1)
