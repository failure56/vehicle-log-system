import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Get the issue body from environment variable
issue_body = os.environ["ISSUE_BODY"]

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

res = client.responses.create(
    model="gpt-4.1-mini",
    input=prompt,
)

print(res.output_text)
