#!/usr/bin/env python3
"""
token-saver SessionStart hook — claude-md-guard.

Warns (never blocks) if CLAUDE.md exceeds 3000 characters.
Always exits 0 — SessionStart cannot block.

Exit codes:
  0 - Always (warning only)
"""

import json
import os
import sys
from pathlib import Path

MAX_CHARS = 3000
MAX_WORDS = 500

WARNING_TEMPLATE = """\
[token-saver] \u26a0\ufe0f CLAUDE.md is ~{char_count} chars (~{word_count} words).
Recommended maximum: {max_chars} chars (~{max_words} words).

Large CLAUDE.md files waste tokens every session because Claude reads
the entire file at startup. Consider moving detailed content to:
  - .claude/skills/<skill-name>/SKILL.md  (for behavioral rules)
  - .claude/memory/                       (for project knowledge)
  - docs/                                 (for reference documentation)

Keep CLAUDE.md focused: 5 rules + 3 file pointers is the right size."""


def find_claude_md() -> "Path | None":
    """Find CLAUDE.md in project root."""
    # Try CLAUDE_PROJECT_DIR first
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        candidate = Path(project_dir) / "CLAUDE.md"
        if candidate.is_file():
            return candidate

    # Fall back to cwd
    cwd_claude_md = Path.cwd() / "CLAUDE.md"
    if cwd_claude_md.is_file():
        return cwd_claude_md

    return None


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    claude_md = find_claude_md()
    if claude_md is None:
        sys.exit(0)

    try:
        content = claude_md.read_text()
    except (OSError, IOError):
        sys.exit(0)

    char_count = len(content)
    if char_count > MAX_CHARS:
        word_count = len(content.split())
        print(WARNING_TEMPLATE.format(
            char_count=char_count,
            word_count=word_count,
            max_chars=MAX_CHARS,
            max_words=MAX_WORDS,
        ), file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
