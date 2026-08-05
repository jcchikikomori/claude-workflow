---
name: memory-guard
description: Guides Claude through the memory-guard flow when a watched .claude/**, root CLAUDE.md, or docs/ticket-tracking/** path is flagged by the memory-guard hooks — save the change to memory, then ask the user to keep or stash it.
---

# memory-guard

When a `SessionStart` or `PostToolUse` hook flags one or more watched paths
(under `.claude/`, the project's root `CLAUDE.md`, or `docs/ticket-tracking/`),
follow this procedure exactly.

## Procedure

1. **Collect every path flagged so far this turn.** If several watched files
   changed in one turn, handle them together in a single pass — one memory
   review and one question to the user, not one interruption per file.

2. **For each path, judge memory-worthiness from the actual diff** (the
   `old_string`/`new_string` from the Edit that triggered the flag, or
   `git diff -- <path>` if you need to see the full change):
   - **Skip** (do not save) pure whitespace/formatting/reflow, typo fixes with
     no semantic change, or a reorder of existing content with nothing new.
   - **Save** when the diff adds a rule, convention, decision, constraint
     ("must", "never", "always", "policy"), a credential/URL/environment
     detail, or a ticket-tracking status/scope note.

3. **Save each memory-worthy change:**
   - Check whether any `mempalace_*` tools are present in your current tool
     roster. If so, call `mempalace_check_duplicate` first, then
     `mempalace_add_drawer` with the content **verbatim** (wing = project,
     room = something like `decisions` or `conventions`).
   - If `mempalace_*` tools are not available, fall back to the file-based
     auto-memory system already described in the user's global CLAUDE.md
     ("Memory — Dual-Layer System"): write or append a
     `~/.claude/projects/<project-slug>/memory/project_<slug>.md` (or
     `feedback_<slug>.md` if the change reads as a behavioral rule rather
     than a project fact), then add one line to that project's `MEMORY.md`
     index in the same style as its existing entries.

4. **Ask the user once**, covering every flagged path together, via
   `AskUserQuestion`: **Keep** these `.claude`-scoped changes as they are, or
   **Stash** them (`git stash`, scoped only to the flagged paths — nothing
   else in the working tree is touched).

5. **Mark each path resolved** so the hooks stop re-flagging it this session.
   Run the exact command the hook's instruction text gave you, e.g.:

   ```bash
   python3 <mark_resolved.py path from the instruction> --session-id <id> --path "<relpath>" --action keep
   ```

   (or `--action stash`, matching what the user chose).

6. **If the user chose Stash**, recompute the live dirty list immediately
   before stashing — never trust the hook's recorded list, in case something
   changed between the flag and now:

   ```bash
   git status --porcelain -- .claude CLAUDE.md docs/ticket-tracking
   ```

   Then stash only the paths that come back dirty, as separate arguments
   (never a shell string), always with `-u` so newly created untracked files
   under `.claude/` are included:

   ```bash
   git stash push -u -- <path1> <path2> ...
   ```

   If the recomputed list is empty (already resolved another way), do
   nothing — never run a bare `git stash push` with no pathspec, since that
   would stash the entire working tree.

## Rules

- Never expand the stash to more than the flagged, currently-dirty watched
  paths. This guard exists specifically so unrelated work is never swept up.
- Don't ask the user one question per file — batch flagged paths from the
  same turn into a single `AskUserQuestion` call.
- Don't save trivial/cosmetic diffs to memory — that defeats the point of
  having a memory-worthiness filter.
- `docs/ticket-tracking/**` files are documented elsewhere as things that
  must never be committed — when in doubt for those specifically, lean
  toward recommending Stash rather than Keep, since it's the safer default
  for content that shouldn't linger in the working tree either.
