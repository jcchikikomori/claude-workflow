#!/usr/bin/env python3
"""
memory-guard PostToolUse hook. Matcher: Write|Edit|MultiEdit.

Fires right after Claude writes/edits a file. If the file is a watched path
(.claude/**, root CLAUDE.md, docs/ticket-tracking/**) and hasn't already been
flagged this session, emits an instruction via the modern
hookSpecificOutput.additionalContext protocol and exits 0.

Deliberately does NOT use the stderr + exit(2) block style that
plugin-commit-guard uses for its PreToolUse hook: the write has already
happened by the time PostToolUse runs, so there's nothing left to block --
exit(2) for PostToolUse was replaced by the additionalContext protocol
upstream (see the shipped security-guidance plugin, which uses the same
shape for the same event/matcher). exit(2)+stderr is still the right choice
for a PreToolUse hook like commit-guard's, which blocks the action itself.
"""

import json
import os
import sys

from memory_guard_common import (
    is_watched,
    mark_pending_if_new,
    plugin_root,
    relpath_or_none,
    repo_root_for,
)

INSTRUCTION = """\
[memory-guard] Watched file just changed: {path}

Session: {session_id}

Run the memory-guard procedure (see the memory-guard skill) for this path
before ending your turn: judge whether the change is memory-worthy, save it
(mempalace if available, otherwise the file-based auto-memory system), then
ask the user once (batched with any other watched files flagged this turn)
whether to KEEP it as-is or STASH it (git stash push -u -- <only the flagged
watched paths>).

Once the user answers, run:
  python3 {mark_resolved} --session-id {session_id} --path "{path}" --action <keep|stash>"""


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd") or os.getcwd()

    if tool_name not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    file_path = tool_input.get("file_path")
    if not file_path:
        sys.exit(0)

    repo_root = repo_root_for(cwd)
    if not repo_root:
        sys.exit(0)

    rel_path = relpath_or_none(file_path, cwd, repo_root)
    if not rel_path or not is_watched(rel_path):
        sys.exit(0)

    if not mark_pending_if_new(session_id, rel_path):
        sys.exit(0)  # already flagged (pending or resolved) this session -- stay silent

    mark_resolved_path = plugin_root() / "scripts" / "mark_resolved.py"
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": INSTRUCTION.format(
                path=rel_path, session_id=session_id, mark_resolved=mark_resolved_path
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
