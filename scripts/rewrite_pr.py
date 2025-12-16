import os
import sys
from openai import OpenAI

# Validate required environment variables
api_key = os.environ.get("OPENAI_API_KEY")
pr_body = os.environ.get("PR_BODY")

if not api_key:
    print("Error: OPENAI_API_KEY environment variable is not set", file=sys.stderr)
    sys.exit(1)

if not pr_body:
    print("Error: PR_BODY environment variable is not set", file=sys.stderr)
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Create the prompt for rewriting the PR description
# Note: PR prompt format differs from Issue prompt because PRs focus on
# implementation details (変更内容, テスト, 注意点) while Issues focus on
# requirements (要件, 非要件, 受け入れ条件)
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

PR説明:
<<<
{pr_body}
>>>
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
