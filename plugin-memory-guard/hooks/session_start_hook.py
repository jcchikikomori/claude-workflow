#!/usr/bin/env python3
"""
memory-guard SessionStart hook.

Detects .claude/**, root CLAUDE.md, and docs/ticket-tracking/** paths that
are ALREADY dirty in git when a session starts (left over from a previous
session, or edited outside Claude). Prints plain instruction text to stdout
on exit 0 -- SessionStart cannot block anything (nothing has happened yet
to block), it can only surface context for Claude to act on, which is the
same mechanism this session's own SessionStart hooks use.
"""

import json
import sys

from memory_guard_common import (
    is_watched,
    load_watched_patterns,
    mark_pending_if_new,
    maybe_gc_old_sessions,
    plugin_root,
    repo_root_for,
    watched_pathspecs,
)

try:
    import subprocess
except ImportError:  # pragma: no cover - stdlib, always present
    subprocess = None

INSTRUCTION = """\
[memory-guard] Watched files were already dirty before this session started:
{paths}

Session: {session_id}

Before doing anything else, run the memory-guard procedure (see the
memory-guard skill): for each path above, judge whether the change is
memory-worthy, save it (mempalace if available, otherwise the file-based
auto-memory system), then ask the user once whether to KEEP these files as
they are or STASH them (git stash push -u -- <only these paths>).

Once the user answers, for each path above run:
  python3 {mark_resolved} --session-id {session_id} --path "<path>" --action <keep|stash>"""


def parse_porcelain_paths(output: str) -> "list[str]":
    paths = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        entry = line[3:]
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        entry = entry.strip()
        if entry.startswith('"') and entry.endswith('"'):
            entry = entry[1:-1]
        paths.append(entry)
    return paths


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd") or "."

    maybe_gc_old_sessions()

    repo_root = repo_root_for(cwd)
    if not repo_root or subprocess is None:
        sys.exit(0)

    try:
        result = subprocess.run(
            ["git", "-C", repo_root, "status", "--porcelain", "--", *watched_pathspecs()],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        sys.exit(0)

    if result.returncode != 0:
        sys.exit(0)

    watched_dirs, watched_files = load_watched_patterns()
    dirty_paths = [
        p for p in parse_porcelain_paths(result.stdout)
        if is_watched(p, watched_dirs, watched_files)
    ]

    newly_flagged = [p for p in dirty_paths if mark_pending_if_new(session_id, p)]

    if newly_flagged:
        listing = "\n".join(f"  - {p}" for p in newly_flagged)
        mark_resolved_path = plugin_root() / "scripts" / "mark_resolved.py"
        print(INSTRUCTION.format(paths=listing, session_id=session_id, mark_resolved=mark_resolved_path))

    sys.exit(0)


if __name__ == "__main__":
    main()
