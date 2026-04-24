#!/usr/bin/env python3
"""
claude-attribution PreToolUse hook.

Blocks external posts that lack the "🤖 Written by Claude, reviewed by <user>"
attribution line. Works dynamically with ANY MCP server.

Exit codes:
  0 - Allow the tool call to proceed
  2 - Block the tool call; stderr message is fed back to Claude as context
"""

import json
import re
import sys
from pathlib import Path

NAME_FILE = Path.home() / ".claude" / "claude-attribution-name.txt"

# Fields that typically contain postable text body.
# Checked in order — first non-empty match wins.
BODY_FIELDS = [
    "body",
    "content",
    "message",
    "comment",
    "commentBody",
    "description",
    "text",
]

# Bash patterns that post to external platforms
POSTING_BASH_PATTERNS = [
    r"\bgh\s+pr\s+(create|comment|review|edit)\b",
    r"\bgh\s+issue\s+(create|comment|edit)\b",
    r"\bgh\s+api\b.*(-f\s+body=|--field\s+body=|-F\s+body=|--raw-field\s+body=)",
    r"\bcurl\s+.*-X\s*(POST|PUT|PATCH)",
    r"\bcurl\s+.*--data",
    r"\bjira\s+issue\s+(create|comment)",
]

SETUP_MESSAGE = """\
[claude-attribution] BLOCKED: Reviewer name not configured.

Before posting to external platforms, set up your attribution name.
Ask the user for their name and save it:

  echo "Their Name" > ~/.claude/claude-attribution-name.txt

Then show the complete post content to the user for approval before retrying."""

MISSING_MESSAGE = """\
[claude-attribution] BLOCKED: Attribution line missing from post body.

All external posts must include this attribution line:

  🤖 Written by Claude, reviewed by {name}

IMPORTANT: Before retrying, you MUST:
1. Add the attribution line to the post body
2. Show the COMPLETE post content to the user
3. Ask the user to approve before posting
4. Only retry after user confirms"""


def get_reviewer_name() -> "str | None":
    try:
        name = NAME_FILE.read_text().strip()
        return name or None
    except FileNotFoundError:
        return None


def find_body_field(tool_input: dict) -> "tuple[str, str] | None":
    for field in BODY_FIELDS:
        value = tool_input.get(field)
        if isinstance(value, str) and value.strip():
            return (field, value)
    return None


def has_attribution(text: str, name: str) -> bool:
    pattern = re.compile(
        r"(\U0001f916\s*)?written\s+by\s+claude.*reviewed\s+by\s+"
        + re.escape(name),
        re.IGNORECASE,
    )
    return bool(pattern.search(text))


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name: str = data.get("tool_name", "")
    tool_input: dict = data.get("tool_input", {})

    # --- Bash: only check posting CLI commands ---
    if tool_name == "Bash":
        command: str = tool_input.get("command", "")
        is_posting = any(
            re.search(p, command, re.IGNORECASE) for p in POSTING_BASH_PATTERNS
        )
        if not is_posting:
            sys.exit(0)

        name = get_reviewer_name()
        if not name:
            print(SETUP_MESSAGE, file=sys.stderr)
            sys.exit(2)
        if not has_attribution(command, name):
            print(MISSING_MESSAGE.format(name=name), file=sys.stderr)
            sys.exit(2)
        sys.exit(0)

    # --- MCP tools: dynamic body field detection ---
    if not tool_name.startswith("mcp__"):
        sys.exit(0)

    result = find_body_field(tool_input)
    if result is None:
        sys.exit(0)

    _field_name, body_text = result

    name = get_reviewer_name()
    if not name:
        print(SETUP_MESSAGE, file=sys.stderr)
        sys.exit(2)

    if not has_attribution(body_text, name):
        print(MISSING_MESSAGE.format(name=name), file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
