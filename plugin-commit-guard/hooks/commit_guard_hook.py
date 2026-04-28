#!/usr/bin/env python3
"""
commit-guard PreToolUse hook.

Blocks every `git commit` Bash call until the user explicitly approves it.
Uses a one-time SHA256 token so the retry passes through without a second prompt.

GPG signing is fully preserved: the command is never modified.

Exit codes:
  0 - Allow the tool call to proceed
  2 - Block the tool call; stderr message is fed back to Claude as context
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

TOKEN_FILE = Path.home() / ".claude" / ".commit-guard-token"

GIT_COMMIT_PATTERN = re.compile(r"\bgit\s+commit\b")

BLOCKED_MESSAGE = """\
[commit-guard] BLOCKED: git commit requires user approval.

Before running this commit, you MUST:
1. Run: git diff --cached --stat
2. Run: git diff --cached --name-only
3. Extract the commit message from the command (the -m "..." value), or note that it uses an editor/template
4. Show the user:
   - Staged files (from step 1 and 2)
   - Commit message (from step 3)
   - The exact command you are about to run
5. Ask the user: "Proceed with this commit?"
6. If the user says YES:
   - Write the approval token:
     python3 -c "import hashlib,sys,pathlib; p=pathlib.Path.home()/'.claude'/'.commit-guard-token'; p.parent.mkdir(exist_ok=True); p.write_text(hashlib.sha256(sys.argv[1].encode()).hexdigest())" "{command}"
   - Then retry the EXACT same command unchanged
7. If the user says NO: abort. Do NOT retry.

IMPORTANT — GPG signing policy:
  - Never add --no-gpg-sign or -c commit.gpgsign=false
  - Never strip -S or --gpg-sign from the command
  - If the repo requires signed commits, git will invoke gpg-agent/pinentry after approval
  - The user will enter their passphrase through the normal pinentry dialog"""


def compute_hash(command: str) -> str:
    return hashlib.sha256(command.encode()).hexdigest()


def read_token() -> "str | None":
    try:
        token = TOKEN_FILE.read_text().strip()
        return token or None
    except FileNotFoundError:
        return None


def consume_token() -> None:
    try:
        TOKEN_FILE.unlink()
    except FileNotFoundError:
        pass


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name: str = data.get("tool_name", "")
    tool_input: dict = data.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command: str = tool_input.get("command", "")

    if not GIT_COMMIT_PATTERN.search(command):
        sys.exit(0)

    token = read_token()
    if token is not None and token == compute_hash(command):
        consume_token()
        sys.exit(0)

    print(BLOCKED_MESSAGE.format(command=command), file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
