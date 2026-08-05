# memory-guard

A Claude Code plugin that watches `.claude/**`, the project's root
`CLAUDE.md`, and `docs/ticket-tracking/**` for changes. When one of those
paths changes — whether Claude just edited it, or it was already dirty when
a session starts — it has Claude save the substance of the change to memory,
then asks the user whether to keep the change or stash it.

## What it does

- **`SessionStart`** hook: checks `git status` for watched paths that are
  already dirty when a session begins (left over from a previous session,
  or edited outside Claude).
- **`PostToolUse`** hook (matcher `Write|Edit|MultiEdit`): fires live,
  immediately after Claude writes/edits a watched path during the session.
- Either way, Claude is instructed to:
  1. Judge whether the change is memory-worthy (skips pure formatting/typo
     noise).
  2. Save it — via the `mempalace` MCP tools if they're available in the
     session, otherwise the existing file-based auto-memory system.
  3. Ask the user once, via `AskUserQuestion`: **Keep** or **Stash**.
  4. If **Stash**: `git stash push -u --` scoped to only the flagged,
     currently-dirty watched paths — never the whole working tree.
- A per-session state file debounces re-prompts: once a path is flagged, it
  won't be flagged again for the rest of that session, so editing the same
  file repeatedly in one turn only triggers the flow once.

## Watch scope

Configurable in `config/watched-paths.json`:

```json
{
  "watched_dirs": [".claude", "docs/ticket-tracking"],
  "watched_files": ["CLAUDE.md"]
}
```

`watched_files` matches only at the repo root (a nested `packages/foo/CLAUDE.md`
won't match); `watched_dirs` matches recursively, the same way a bare
directory pathspec does in `git`.

## Install

```bash
/plugin install memory-guard@claude-workflow
/reload-plugins
```

## How it works

| Component | Path | Role |
| ----------- | ------ | ------ |
| Hook | `hooks/session_start_hook.py` | Detects stale dirty watched paths at session start |
| Hook | `hooks/post_tool_use_hook.py` | Detects live watched-path writes/edits |
| Shared module | `hooks/memory_guard_common.py` | Repo-root resolution, path matching, locked session-state I/O |
| Hook config | `hooks/hooks.json` | Registers `SessionStart` (no matcher) + `PostToolUse` (`Write\|Edit\|MultiEdit`) |
| Helper | `scripts/mark_resolved.py` | Claude runs this after the user answers keep/stash |
| Config | `config/watched-paths.json` | Editable watch-path list |
| Skill | `skills/memory-guard/SKILL.md` | The save-then-ask procedure Claude follows |
| State | `~/.claude/.memory-guard/session_<id>.json` | Per-session flagged/resolved path tracking |

## Known limitations

- No filesystem watcher: a file edited in another editor mid-session, with
  Claude making no tool calls, is only caught at the *next* `SessionStart`,
  not live.
- Gitignored watched paths (e.g. a gitignored `.claude/settings.local.json`)
  are invisible to `git status`, so stale-change detection has a blind spot
  there.
- If the project isn't inside a git repo, the stash-offering path no-ops;
  the memory-save side can still run.

## Changelog

### 0.1.0

Initial release. `SessionStart` + `PostToolUse` detection, per-session
debounce, mempalace-or-fallback memory save, scoped keep/stash prompt.
