#!/usr/bin/env python3
"""
token-saver UserPromptSubmit hook — prompt-quality.

Blocks vague prompts and guides the user to be specific.
Checks against configurable patterns in config/vague-patterns.json.

Exit codes:
  0 - Allow the prompt to proceed
  2 - Block the prompt; stderr message is fed back to Claude as context
"""

import json
import os
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent))
PATTERNS_FILE = PLUGIN_ROOT / "config" / "vague-patterns.json"

BLOCK_MESSAGE = """\
[token-saver] BLOCKED: This prompt is too vague — it will cost extra tokens
for Claude to figure out what you mean.

Please provide specifics:
  - File paths (e.g. src/auth/login.ts)
  - Line numbers (e.g. line 45)
  - Function names (e.g. handleSubmit)
  - Error messages (e.g. "TypeError: Cannot read property 'map'")

Bad:  "fix the bug"
Good: "Fix the null pointer in src/auth/login.ts line 45 — handleSubmit called before useState resolves"

Bad:  "make it better"
Good: "Optimize the N+1 query in app/models/user.rb — User#orders loads each order individually"

Bad:  "handle the error"
Good: "Add error handling for the failed fetch in components/Dashboard.tsx — catch the network error and show a retry button" """


def load_patterns() -> "tuple[list[str], list[str]]":
    """Load vague patterns and whitelisted prefixes from config file."""
    try:
        data = json.loads(PATTERNS_FILE.read_text())
        patterns = data.get("patterns", [])
        whitelisted = data.get("whitelisted_prefixes", [])
        return patterns, whitelisted
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback defaults
        return [
            "fix the bug", "fix the error", "make it better",
            "handle the error", "just do it", "figure it out",
            "optimize this", "clean this up", "update this",
            "add the thing", "make it work", "solve this",
            "handle this", "do the thing", "fix this",
            "improve this", "refactor this",
        ], ["fix ", "add ", "create ", "update ", "remove ", "change ", "refactor "]


def is_vague(prompt: str, patterns: list[str], whitelisted: list[str]) -> bool:
    """Check if a prompt matches vague patterns but not whitelisted prefixes."""
    prompt_lower = prompt.lower().strip()

    # Check whitelisted prefixes first — if prompt starts with one, it's specific enough
    for prefix in whitelisted:
        if prompt_lower.startswith(prefix):
            # "fix X" is okay if X is specific (more than just "the bug")
            remainder = prompt_lower[len(prefix):].strip()
            # If the remainder is short and matches a vague pattern, still vague
            if remainder in [p[len(prefix):].strip() for p in patterns if p.startswith(prefix)]:
                return True
            # If remainder has meaningful content (file paths, line numbers, function names), allow
            if len(remainder) > 20 or any(c in remainder for c in "./_()"):
                return False
            # Short remainder after prefix — could be vague
            if len(remainder.split()) <= 3:
                return True
            return False

    # Check exact matches against vague patterns
    for pattern in patterns:
        if prompt_lower == pattern:
            return True

    # Check if prompt is very short and lacks specificity markers
    if len(prompt_lower) < 15 and not any(c in prompt_lower for c in "./_:()"):
        return True

    return False


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input: dict = data.get("tool_input", {})
    prompt: str = tool_input.get("prompt", "")

    if not prompt.strip():
        sys.exit(0)

    patterns, whitelisted = load_patterns()

    if is_vague(prompt, patterns, whitelisted):
        print(BLOCK_MESSAGE, file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
