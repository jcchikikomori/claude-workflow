#!/usr/bin/env python3
"""
Claude runs this after applying the remove/stash action to a flagged path,
to mark it "resolved" in its session state file so the PostToolUse/
SessionStart hooks stop flagging it for the rest of the session.

Usage:
  python3 mark_resolved.py --session-id <id> --path <relpath> --action remove|stash
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))

from memory_guard_common import mark_resolved  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--action", required=True, choices=["remove", "stash"])
    args = parser.parse_args()

    mark_resolved(args.session_id, args.path, args.action)
    print(f"[memory-guard] marked {args.path!r} resolved ({args.action}) for session {args.session_id}")


if __name__ == "__main__":
    main()
