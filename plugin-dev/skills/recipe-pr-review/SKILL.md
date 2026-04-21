---
name: recipe-pr-review
description: Full PR review with codebase context loading — fetches PR data, scans affected areas for existing patterns, loads prior learnings, delegates to pr-reviewer for deep analysis, then optionally posts inline comments to GitHub
disable-model-invocation: true
---

**Context**: External PR review grounded in codebase conventions

PR identifier: $ARGUMENTS

## Orchestrator Definition

**Core Identity**: "I am an orchestrator." (see subagents-orchestration-guide skill)

**First Action**: Register Steps 1–8 using TaskCreate before any execution.

## Pre-execution Parse

Extract from `$ARGUMENTS`:

| Input Form | Extraction |
|---|---|
| Full GitHub URL (`https://github.com/owner/repo/pull/123`) | owner, repo, PR number |
| `owner/repo#123` | owner, repo, PR number |
| Bare number (`123`) | PR number only — infer repo from `git remote get-url origin` |
| Branch name | Resolve via `mcp__github__list_pull_requests` filtered by head branch |

If repo cannot be determined, use AskUserQuestion to ask the user before proceeding.

## Execution Flow

### Step 1: Prerequisite Check

Register all steps using TaskCreate. Update each using TaskUpdate as it begins.

```bash
git remote get-url origin
git status --short
```

### Step 2: Fetch PR Metadata

Use `mcp__github__pull_request_read` with owner, repo, pull_number.

Extract and store as `$PR_META`:
- `title`, `body`, `state`, `base.ref`, `head.ref`, `user.login`
- `changed_files` count, `additions`, `deletions`

Fetch the changed files list (filename, status, additions, deletions, patch). Store as `$CHANGED_FILES`.

If PR is `closed` or `merged`: warn the user and use AskUserQuestion to ask whether to proceed.

### Step 3: Codebase Context Scan

**Purpose**: Prime the review with existing patterns so the agent does not review in a vacuum.

For each file in `$CHANGED_FILES`, identify its layer from path:
- `tests/`, `*spec*`, `*test*`, `__tests__/`, `_test.` → test file
- `src/`, `lib/`, `app/` → application code
- `.github/`, `*.yml`, `*.json` at root → config/infrastructure
- `docs/` → documentation

Then fetch reference files (≤5 total across all files):

1. **App files** — use `mcp__github__get_file_contents` to fetch 1–2 sibling files (unchanged) from the same directory. Extract: naming conventions, error handling style, import patterns, function signature shape.

2. **Test files** — fetch 1–2 existing test files from the same test directory. Extract: test framework, assertion library, describe/it vs test() style, mock patterns, AAA structure usage.

3. **CLAUDE.md** — read if present at repo root via `mcp__github__get_file_contents`. Contains explicit project conventions.

4. **Package manifest** — read `package.json` / `Gemfile` / `requirements.txt` / `go.mod` for language and framework context.

Compile `$CODEBASE_CONTEXT`:
```json
{
  "language": "",
  "framework": "",
  "testFramework": "",
  "namingConventions": "",
  "errorHandlingPattern": "",
  "importStyle": "",
  "testPatterns": "",
  "notableConventions": [],
  "existingSampleFiles": []
}
```

### Step 4: Load Prior Learnings

Invoke context-scouter using Agent tool:
- `subagent_type`: "dev:context-scouter"
- `description`: "Load PR review learnings"
- `prompt`: "Retrieve all memories related to: PR review gotchas, recurring code issues, project conventions, past review findings for repo [owner/repo]. Return a concise list of learnings to inform the current review."

**Store output as**: `$PRIOR_LEARNINGS`

### Step 5: Invoke pr-reviewer

Invoke pr-reviewer using Agent tool:
- `subagent_type`: "dev:pr-reviewer"
- `description`: "Deep PR review with context"
- `prompt`:
```
PR Metadata:
- Title: [title]
- Author: [user.login]
- Base branch: [base.ref]
- PR body: [body]
- Stats: [changed_files] files, +[additions]/-[deletions]

Changed Files with Diffs:
[For each entry in $CHANGED_FILES: filename, status, patch]

Codebase Context:
[Full $CODEBASE_CONTEXT JSON]

Prior Learnings from Past Reviews:
[Full $PRIOR_LEARNINGS — empty if first review for this repo]

Instructions:
- Validate each change against the codebase patterns in Codebase Context
- Apply prior learnings as additional review criteria where relevant
- Apply coding-principles and testing-principles skills during review
- Return structured JSON matching the pr-reviewer output schema
```

**Store output as**: `$REVIEW_OUTPUT`

### Step 6: Present Structured Report

Parse `$REVIEW_OUTPUT` and render using [Conventional Comments](https://conventionalcomments.org/) labels:

Label mapping from `severity` + `category`:
- `critical` + `security` → `issue (blocking, security):`
- `critical` other → `issue (blocking):`
- `major` → `issue:`
- `minor` → `nitpick (non-blocking):`
- `suggestion` → `suggestion:`

```
## PR Review: [title]
URL: https://github.com/[owner]/[repo]/pull/[number]
Author: [user.login] | Files: [changed_files] | +[additions]/-[deletions]

Verdict: [APPROVE / REQUEST CHANGES / COMMENT]

---

### Findings ([total] total)

[Group by severity: critical → major → minor → suggestion]

[label (decorations)]: [description]
  `[file]:[line]` | [category]
  > [rationale]
  > Fix: [suggestion text]

---

### Summary
Critical: [n]  Major: [n]  Minor: [n]  Suggestions: [n]
By category: standards=[n] consistency=[n] testing=[n] security=[n] performance=[n] logic=[n]

---

Post inline comments to GitHub? (y/n):
```

### Step 7: Post Inline Comments (Conditional)

If user selects `y`:

1. Create pending review: `mcp__github__pull_request_review_write` (method: `create`)
2. For each finding with a `file` and `line`, add inline comment: `mcp__github__add_comment_to_pending_review`
   - `path`: finding.file
   - `line`: finding.line
   - `body`: "[label (decorations)]: [description]\n> [rationale]\n\n[suggestion]"\n     (derive label from severity+category using the mapping in Step 6)
   - The `[suggestion]` field from the finding already contains the text line + ` ```suggestion ` code block — paste it verbatim
3. Ask user: "Submit review with verdict `[verdict]`, or leave as pending draft for you to submit manually? (submit/leave)"
   - `submit` → `mcp__github__pull_request_review_write` (method: `submit_pending`) with event = `APPROVE` / `REQUEST_CHANGES` / `COMMENT` per verdict; report submitted review URL
   - `leave` → report "Review draft created at [url]. Submit it manually on GitHub when ready." No further writes.

If user selects `n`: skip to Step 8.

### Step 8: Persist Learnings

Invoke context-keeper using Agent tool:
- `subagent_type`: "dev:context-keeper"
- `description`: "Persist PR review learnings"
- `prompt`:
```
Capture learnings from this PR review session.

Repo: [owner/repo]
PR: [title] (#[number])
Findings summary: [bySeverity counts] | [byCategory counts]
Notable findings (critical/major):
[List each critical and major finding: file, category, description]

Conventions detected:
[conventionsDetected JSON from $REVIEW_OUTPUT]

Save as:
- feedback memories: recurring issues or patterns worth watching in future reviews
- project memories: confirmed conventions for this repo tagged to [owner/repo]
Skip findings that are one-off or too specific to this PR to generalize.
```

## Scope

External PR review grounded in codebase conventions and accumulated learnings. No Design Doc required.
