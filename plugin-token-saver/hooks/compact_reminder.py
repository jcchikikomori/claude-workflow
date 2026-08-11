#!/usr/bin/env python3
"""
token-saver PostToolUse hook — compact-reminder.

Tracks timestamps and prints a nudge to run /compact every ~15 minutes.
Always exits 0 — this is a non-blocking reminder.

Exit codes:
  0 - Always (non-blocking nudge)
"""

import json
import os
import sys
import time
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / ".token-saver"
COMPACT_INTERVAL_SECONDS = 15 * 60  # 15 minutes

REMINDER_MESSAGE = """\
**\U0001f4a1 Token-saving tip:** It's been ~15 minutes since last compaction. Consider running `/compact` now to keep context lean and reduce token costs.

When to compact:
- After 5+ file reads or exploration phases
- Before switching from investigation to implementation
- When context feels cluttered with intermediate results

When NOT to compact:
- Mid-implementation (you need the context)
- Right before a critical edit (keep the plan visible)"""


def get_state_path(session_id: str) -> Path:
    return STATE_DIR / f"last-compact-{session_id}.json"


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def read_last_compact(session_id: str) -> "float | None":
    state_path = get_state_path(session_id)
    try:
        data = json.loads(state_path.read_text())
        return data.get("timestamp")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def write_last_compact(session_id: str) -> None:
    state_path = get_state_path(session_id)
    state_path.write_text(json.dumps({
        "session_id": session_id,
        "timestamp": time.time(),
    }))


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    session_id = data.get("session_id", "default")

    ensure_state_dir()

    last_compact = read_last_compact(session_id)
    now = time.time()

    if last_compact is None or (now - last_compact) >= COMPACT_INTERVAL_SECONDS:
        print(REMINDER_MESSAGE)

    # Always update timestamp (each tool call resets the window)
    write_last_compact(session_id)

    sys.exit(0)


if __name__ == "__main__":
    main()
