---
name: token-saver
description: Token-saving behavioral guidance — plan mode, compaction, specificity, delegation, CLAUDE.md limits, effort advice
---

# token-saver

Six techniques to keep token costs low. Three enforced by hooks, three by behavioral guidance.

## Hooks (automatic)

- **compact-reminder** — Nudges you to run `/compact` every ~15 minutes
- **claude-md-guard** — Warns if CLAUDE.md exceeds 3000 chars
- **prompt-quality** — Blocks vague prompts ("fix the bug") and asks for specifics

## Behavioral rules

### 1. Plan first

**Before writing any code or invoking agents, suggest entering plan mode.**

If the user says "just do X" or "implement Y", ask:

> "Should we plan this first? Planning prevents wasted tokens from wrong approaches."

Planning saves tokens by:

- Preventing exploration on the wrong path
- Reducing back-and-forth from misunderstood requirements
- Enabling parallel work from a clear task list

Do NOT plan trivial fixes (typo, config value change). Do plan anything touching 3+ files or multiple components.

### 2. Compact proactively

After 5+ file reads or a long exploration phase, suggest `/compact` before switching to execution. The hook reminds every ~15 minutes, but you should also suggest it at natural breakpoints.

**When to compact:**

- After gathering context (reads, greps, searches)
- Before starting implementation
- When context has stale exploration results

**When NOT to compact:**

- Mid-implementation (you need the context)
- Right before a critical edit (keep the plan visible)

### 3. Be specific

Always ask for file paths, line numbers, function names, or error messages. Never guess when the user can tell you.

| Bad                | Good                                                  |
| ------------------ | ----------------------------------------------------- |
| "fix the bug"      | "Fix null pointer in src/auth/login.ts line 45"       |
| "make it better"   | "Optimize N+1 query in User#orders"                   |
| "handle the error" | "Catch network error in Dashboard.tsx and show retry" |

### 4. Delegate verbose work

If a task produces more than one screen of output (test suites, long logs, documentation generation), suggest using a subagent. This keeps the main context lean.

### 5. Keep CLAUDE.md small

When editing CLAUDE.md, keep it under 3000 characters. Move detailed content to:

- `.claude/skills/<name>/SKILL.md` — behavioral rules
- `.claude/memory/` — project knowledge
- `docs/` — reference documentation

5 rules + 3 file pointers is the right size.

### 6. Lower effort for mechanical tasks

For formatting, renaming, repetitive edits, or boilerplate — suggest the user lower `/effort` or switch to a faster model. Don't use maximum effort for mechanical work.
