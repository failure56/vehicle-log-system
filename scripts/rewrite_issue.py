import os
import sys
from openai import OpenAI

# Validate required environment variables
api_key = os.environ.get("OPENAI_API_KEY")
issue_title = os.environ.get("ISSUE_TITLE", "")
issue_body = os.environ.get("ISSUE_BODY", "")

if not api_key:
    print("Error: OPENAI_API_KEY environment variable is not set", file=sys.stderr)
    sys.exit(1)

# Check if we have at least title or body
if not issue_title and not issue_body:
    print("Error: At least one of ISSUE_TITLE or ISSUE_BODY must be set", file=sys.stderr)
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Create the prompt for rewriting the issue
# If body is empty, infer from title
if issue_body:
    issue_content = f"Issue題名: {issue_title}\n\nIssue本文:\n<<<\n{issue_body}\n>>>"
else:
    issue_content = f"Issue題名: {issue_title}\n\n※本文が記載されていないため、題名から内容を類推してください。"

prompt = f"""
以下は人間が手動で作成した GitHub Issue です。
内容を変更せず、実装者が作業しやすい形にリライトしてください。

ルール:
- 新しい要件は追加しない
- 推測が必要な部分は「未決事項」として分離
- 断定できないことは断定しない

出力形式:
## 概要
## 背景
## 要件
## 非要件
## 受け入れ条件
## 未決事項

{issue_content}
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
