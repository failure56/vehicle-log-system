import os
import sys
from openai import OpenAI

# Validate required environment variables
api_key = os.environ.get("OPENAI_API_KEY")
issue_body = os.environ.get("ISSUE_BODY")

if not api_key:
    print("Error: OPENAI_API_KEY environment variable is not set", file=sys.stderr)
    sys.exit(1)

if not issue_body:
    print("Error: ISSUE_BODY environment variable is not set", file=sys.stderr)
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Create the prompt for rewriting the issue
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

Issue本文:
<<<
{issue_body}
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
