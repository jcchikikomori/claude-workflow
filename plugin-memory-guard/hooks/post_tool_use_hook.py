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

Remove vs stash is asked ONCE per project (see memory_guard_common's project
preference file, stored outside the repo so writing it never itself counts
as a watched-path change) -- every flagged path after that is auto-resolved
using the stored preference, no further AskUserQuestion needed. Actually
applying the resolved action goes through apply_action.py (a single
deterministic script) rather than freeform git commands, since a past
resolution got recorded as done without the underlying git stash ever
actually running.
"""

import json
import os
import sys

from memory_guard_common import (
    is_watched,
    mark_pending_if_new,
    plugin_root,
    read_project_preference,
    relpath_or_none,
    repo_root_for,
)

FIRST_TIME_INSTRUCTION = """\
[memory-guard] Watched file just changed: {path}

Session: {session_id}
Project: {repo_root}

No remove/stash preference is set for this project yet. Run the
memory-guard procedure (see the memory-guard skill) for this path before
ending your turn: judge whether the change is memory-worthy, save it
(mempalace if available, otherwise the file-based auto-memory system), then
ask the user ONCE (batched with any other watched files flagged this turn):
should watched .claude-scoped changes in this project be REMOVED (deleted
from disk, content already preserved in memory) or STASHed (git stash,
scoped only to watched paths) going forward? This question is asked only
this one time for this project -- the answer is then persisted and reused
automatically for every future flagged path here.

This AskUserQuestion is mandatory even if the current session says to work
autonomously without stopping to ask -- that bias covers ordinary judgment
calls, not this explicit user-requested gate. Do not silently pick an
action and continue without asking.

Once the user answers, persist it, then apply it in one step (this actually
performs the deletion/stash and marks every currently-dirty watched path
resolved -- do not hand-write git commands instead):
  python3 {set_preference} --repo-root "{repo_root}" --action <remove|stash>
  python3 {apply_action} --repo-root "{repo_root}" --action <remove|stash> --session-id {session_id}"""

AUTO_APPLY_INSTRUCTION = """\
[memory-guard] Watched file just changed: {path}

Session: {session_id}
Project preference already set: {action}

No need to ask -- this project already has a standing preference. Run the
memory-guard procedure (see the memory-guard skill) for this path: judge
whether the change is memory-worthy, save it (mempalace if available,
otherwise the file-based auto-memory system), then run the one command
below to actually apply "{action}" and mark it resolved -- do not
hand-write git commands instead:
  python3 {apply_action} --repo-root "{repo_root}" --action {action} --session-id {session_id}"""


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

    apply_action_path = plugin_root() / "scripts" / "apply_action.py"
    preference = read_project_preference(repo_root)

    if preference is None:
        set_preference_path = plugin_root() / "scripts" / "set_preference.py"
        text = FIRST_TIME_INSTRUCTION.format(
            path=rel_path,
            session_id=session_id,
            repo_root=repo_root,
            set_preference=set_preference_path,
            apply_action=apply_action_path,
        )
    else:
        text = AUTO_APPLY_INSTRUCTION.format(
            path=rel_path,
            session_id=session_id,
            repo_root=repo_root,
            action=preference,
            apply_action=apply_action_path,
        )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": text,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
