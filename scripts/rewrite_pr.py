import json
import os
import sys
import urllib.error
import urllib.request


def load_project_context(path: str = ".github/copilot-instructions.md") -> str:
    """copilot-instructions.md のマーカー区間からプロジェクト固有コンテキストを抽出する。"""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return ""
    start_marker = "<!-- ai-context:start -->"
    end_marker = "<!-- ai-context:end -->"
    start = content.find(start_marker)
    end = content.find(end_marker)
    if start == -1 or end == -1:
        return ""
    return content[start + len(start_marker):end].strip()


# Validate required environment variables
token = os.environ.get("GITHUB_TOKEN")
pr_title = os.environ.get("PR_TITLE", "")
pr_body = os.environ.get("PR_BODY", "")
pr_diff = os.environ.get("PR_DIFF", "")
pr_files = os.environ.get("PR_FILES", "")
pr_commits = os.environ.get("PR_COMMITS", "")

# PR_BODY からテスト結果マーカー区間を分離（AI に送らず、出力末尾に再付加する）
_TEST_START = "<!-- vehicle-log-system:test-report:start -->"
_TEST_END   = "<!-- vehicle-log-system:test-report:end -->"
_test_section_suffix = ""
if _TEST_START in pr_body and _TEST_END in pr_body:
    _s = pr_body.index(_TEST_START)
    _e = pr_body.index(_TEST_END) + len(_TEST_END)
    _test_section_suffix = "\n\n---\n\n" + pr_body[_s:_e]
    pr_body = pr_body[:_s].rstrip()  # マーカー区間を除去してから AI に渡す
else:
    _test_section_suffix = (
        f"\n\n---\n\n{_TEST_START}\n"
        "> ⏳ テスト結果はCIが完了すると自動で更新されます\n"
        f"{_TEST_END}"
    )

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

# コミットメッセージ一覧（変更の流れ・意図を把握するための最も信頼性の高い情報源）
if pr_commits.strip():
    pr_content += (
        f"\n\nコミットメッセージ一覧:\n"
        f"```\n{pr_commits}\n```"
    )

# 変更ファイル一覧（差分が切り詰められても全ファイルを把握できる）
if pr_files.strip():
    pr_content += (
        f"\n\n変更ファイル一覧:\n"
        f"```\n{pr_files}\n```"
    )

# 差分内容（先頭 N 文字）
if pr_diff.strip():
    pr_content += (
        f"\n\n変更差分（先頭 {len(pr_diff)} 文字）:\n"
        f"```diff\n{pr_diff}\n```"
    )

prompt = f"""
以下の GitHub Pull Request の説明をリライトしてください。

{pr_content}
"""

# system プロンプトで出力形式・ルール・制約を明示的に指定
project_context = load_project_context()
system_prompt = f"""\
あなたはGitHub Pull Requestの編集者です。
ユーザーから渡されるPRの説明・差分を参照し、レビュアーが理解しやすい形にリライトしてください。

{project_context}

# ルール
- 元の意図や内容を変更しないこと
- 新しい要件は追加しない
- 推測が必要な部分は「未決事項」セクションに分離する
- 断定できないことは断定しない
- 変更内容のサマリを追加する
- コミットメッセージが提供されている場合は変更の流れ・意図の推測に活用すること
- 差分が提供されている場合は実際の変更内容を具体的に反映すること
- 差分が切り詰められている場合は「変更ファイル一覧」を参照して不足を補うこと
- 関連するIssueがあれば明記する
- 前置き・後書き・説明文は一切出力しない（Markdownの本文のみ出力すること）
- PRの目的と無関係な変更（スコープ外のリファクタリング、無関係なファイルの変更等）を
  「不要な変更の指摘」セクションに記載すること。該当がない場合は「なし」と記載する
- サブモジュールの変更（`Subproject commit` の変化、`.gitmodules` の変更）は
  意図的かどうかに関わらず必ず「SubModuleの変更」セクションに記載すること。
  差分にサブモジュールの変更が見られない場合は「なし」と記載する
- テスト項目については、含まれるテストが何を確認するのかを具体的に記載すること。
  単に「テストを追加」などと記載するのは不十分であり、レビュアーがテスト内容を理解できるようにすること
  テストとその結果は表としてまとめること。
- 絵文字や装飾は適切に使うこと（多用しすぎないが、OK/NGの判断に役立つ場合は使用可）
- テスト結果についてはタグが付いているので、その情報は必ず活用すること（例: `テスト結果: ✅成功`, `テスト結果: ❌失敗` など）

# 出力形式（必ずこの見出し順で出力すること）
## 概要
## 変更内容
## 関連Issue
## テスト
## 注意点
## SubModuleの変更
## 不要な変更の指摘
## 未決事項
"""

try:
    # Prepare request payload for GitHub Models API (OpenAI-compatible)
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,  # GitHub Models API の上限に合わせた設定
        "temperature": 0.3,

    }

    request_body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        "https://models.inference.ai.azure.com/chat/completions",
        data=request_body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as response:
        response_text = response.read().decode("utf-8")

    res = json.loads(response_text)

    choices = res.get("choices") or []
    if not choices:
        print("Error: GitHub Models API returned no response choices", file=sys.stderr)
        sys.exit(1)

    print(choices[0]["message"]["content"] + _test_section_suffix)
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print(f"Error calling GitHub Models API ({e.code}): {body}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error calling GitHub Models API: {e}", file=sys.stderr)
    sys.exit(1)
