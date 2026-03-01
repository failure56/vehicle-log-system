import json
import os
import sys
import urllib.error
import urllib.request

# Validate required environment variables
token = os.environ.get("GITHUB_TOKEN")
issue_title = os.environ.get("ISSUE_TITLE", "")
issue_body = os.environ.get("ISSUE_BODY", "")

if not token:
    print("Error: GITHUB_TOKEN environment variable is not set", file=sys.stderr)
    sys.exit(1)

# Check if we have at least title or body (after stripping whitespace)
if not issue_title.strip() and not issue_body.strip():
    print("Error: At least one of ISSUE_TITLE or ISSUE_BODY must contain non-whitespace content", file=sys.stderr)
    sys.exit(1)

# Create the prompt for rewriting the issue
# Handle three cases: 1) title+body, 2) body only, 3) title only
if issue_body.strip():
    # Both title and body are present
    if issue_title.strip():
        issue_content = f"Issue題名: {issue_title}\n\nIssue本文:\n<<<\n{issue_body}\n>>>"
    else:
        issue_content = f"Issue本文:\n<<<\n{issue_body}\n>>>"
else:
    # Only title is present
    issue_content = f"Issue題名: {issue_title}\n\n※本文が記載されていないため、題名から内容を類推してください。"

prompt = f"""
以下の GitHub Issue をリライトしてください。

{issue_content}
"""

# system プロンプトで出力形式・ルール・制約を明示的に指定
system_prompt = """\
あなたはGitHub Issueの編集者です。
ユーザーから渡されるIssueの内容を、実装者が作業しやすい形にリライトしてください。
以下の GitHub Issue をリライトしてください。

{issue_content}
"""

# system プロンプトで出力形式・ルール・制約を明示的に指定
system_prompt = """\
あなたはGitHub Issueの編集者です。
ユーザーから渡されるIssueの内容を、実装者が作業しやすい形にリライトしてください。

# ルール
- 元の意図や内容を変更しないこと
- 新しい要件は追加しない
- 推測が必要な部分は「未決事項」セクションに分離する
- 断定できないことは断定しない
- 前置き・後書き・説明文は一切出力しない（Markdownの本文のみ出力すること）

# 出力形式（必ずこの見出し順で出力すること）
## 概要
## 背景
## 要件
## 非要件
## 受け入れ条件
## 未決事項

{issue_content}
"""

try:
    # GitHub Models API endpoint for chat completions
    api_url = "https://api.githubcopilot.com/chat/completions"

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }

    request_body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        api_url,
        data=request_body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2023-07-01",
        },
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        response_text = response.read().decode("utf-8")

    data = json.loads(response_text)

    choices = data.get("choices") or []
    if not choices:
        print("Error: GitHub Models API returned no response choices", file=sys.stderr)
        sys.exit(1)

    print(choices[0]["message"]["content"])
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print(f"Error calling GitHub Models API ({e.code}): {body}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error calling GitHub Models API: {e}", file=sys.stderr)
    sys.exit(1)
