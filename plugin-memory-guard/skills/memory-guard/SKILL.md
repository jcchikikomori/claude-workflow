---
name: memory-guard
description: Guides Claude through the memory-guard flow when a watched .claude/**, root CLAUDE.md, or docs/ticket-tracking/** path is flagged by the memory-guard hooks — save the change to memory, then apply the project's remove/stash preference (asking once, ever, per project, if none is set yet).
---

# memory-guard

When a `SessionStart` or `PostToolUse` hook flags one or more watched paths
(under `.claude/`, the project's root `CLAUDE.md`, or `docs/ticket-tracking/`),
follow this procedure exactly. The hook's injected instruction text tells you
which of the two cases below you're in — read it carefully, it already
checked whether this project has a standing preference.

**The first-time `AskUserQuestion` call (Case A below) is mandatory,
including in Auto Mode or any other "work without stopping to ask" mode.**
That general bias exists for ordinary implementation judgment calls — it
does not apply here. This is a one-time, per-project question the user
explicitly asked for; silently picking an action and continuing is not an
acceptable substitute, no matter what session mode is active.

## Case A — no project preference set yet (first time ever for this repo)

1. **Collect every path flagged so far this turn.** Handle them together in
   one pass — one memory review and one question, not one interruption per
   file.

2. **For each path, judge memory-worthiness** from the actual diff (the
   `old_string`/`new_string` from the Edit that triggered the flag, or
   `git diff -- <path>` for the full change):
   - **Skip** pure whitespace/formatting/reflow, typo fixes with no semantic
     change, or a reorder of existing content with nothing new.
   - **Save** when the diff adds a rule, convention, decision, constraint
     ("must", "never", "always", "policy"), a credential/URL/environment
     detail, or a ticket-tracking status/scope note.

3. **Save each memory-worthy change** (see "Saving to memory" below).

4. **Ask the user ONCE** — this is a per-project question, not per-file or
   per-turn — via `AskUserQuestion`: should watched `.claude`-scoped changes
   in *this project* be **Removed** (deleted from disk — the content is
   already preserved in memory, so the working-tree copy is disposable) or
   **Stashed** (`git stash`, scoped only to the flagged paths)? Make clear
   this choice will be remembered and applied automatically for this project
   from now on.

5. **Persist the answer**, then **apply it** to every path flagged this
   turn:

   ```bash
   python3 <set_preference.py path from the instruction> --repo-root "<repo_root>" --action <remove|stash>
   ```

   Then, per path: if **Remove**, delete the file; if **Stash**, do the
   live-recompute-and-stash below.

6. **Mark each path resolved**:

   ```bash
   python3 <mark_resolved.py path from the instruction> --session-id <id> --path "<relpath>" --action <remove|stash>
   ```

## Case B — project preference already set (every time after the first)

The hook's instruction already tells you the standing action
(`remove` or `stash`) — do not ask the user again.

1. Collect every path flagged this turn.
2. For each, judge memory-worthiness and save (see below) — this step still
   happens every time, only the remove/stash *question* is one-time.
3. Apply the standing action directly to each path (delete, or stash — see
   below).
4. Mark each path resolved via `mark_resolved.py`, same as Case A step 6,
   with `--action` matching the standing preference.

## Saving to memory

- Check whether any `mempalace_*` tools are present in your current tool
  roster. If so, call `mempalace_check_duplicate` first, then
  `mempalace_add_drawer` with the content **verbatim** (wing = project,
  room = something like `decisions` or `conventions`).
- If `mempalace_*` tools are not available, fall back to the file-based
  auto-memory system already described in the user's global CLAUDE.md
  ("Memory — Dual-Layer System"): write or append a
  `~/.claude/projects/<project-slug>/memory/project_<slug>.md` (or
  `feedback_<slug>.md` if the change reads as a behavioral rule rather than
  a project fact), then add one line to that project's `MEMORY.md` index in
  the same style as its existing entries.

## The stash (when the action is "stash")

Never stash from the recorded state — always recompute live, immediately
before stashing, so nothing stale or already-reverted gets swept in:

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

## The removal (when the action is "remove")

Only delete the exact flagged path(s) — never a wider glob, never anything
outside the watched-path list. Confirm the memory save from step 2/above
actually happened before deleting; the file is the only copy of that
content until the memory save lands.

## Rules

- Never touch anything beyond the flagged, currently-dirty watched paths —
  this guard exists specifically so unrelated work is never swept up,
  whether by stash or by deletion.
- Don't ask the user one question per file — the whole point of the
  standing preference is that this is asked at most once, ever, per
  project.
- Don't save trivial/cosmetic diffs to memory — that defeats the point of
  having a memory-worthiness filter.
- `docs/ticket-tracking/**` files are documented elsewhere as things that
  must never be committed — if a user hasn't set a preference yet and asks
  for a recommendation, Remove is usually the safer default for those
  specifically, since they shouldn't linger in the working tree either.
- To let a user change their mind later, `scripts/reset_preference.py
  --repo-root <path>` clears the standing preference so the next flagged
  change asks Case A again.
