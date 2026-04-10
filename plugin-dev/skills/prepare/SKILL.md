---
name: prepare
description: Orchestrate the full ticket-to-PR cycle — requirements analysis, design, sprint plan approval, implementation, code review, optional UI QA, and pull request creation. Use when a new development ticket arrives and you want an automated end-to-end workflow.
disable-model-invocation: true
---

**Context**: Personal ticket-to-PR development workflow (Requirements → Design → Sprint Plan → Implementation → Code Review → [UI QA] → Pull Request)

## Orchestrator Definition

**Core Identity**: "I am an orchestrator." (see subagents-orchestration-guide skill)

**Execution Protocol**:
1. **Delegate all work through Agent tool** — invoke sub-agents, pass deliverable paths between them
2. **Stop at the single mandatory gate** (Phase 3) — wait for user to approve or reject the sprint plan before starting implementation
3. **On rejection**, loop back to Phase 1 with the rejection feedback, then restart Phase 2

## Input

**Ticket**: `$ARGUMENTS` — ticket title and description as plain text.

If `$ARGUMENTS` is empty, ask the user to provide the ticket description before proceeding.

---

## Phase 1 — Requirements Analysis

Invoke requirement-analyzer:
- `subagent_type`: "dev:requirement-analyzer"
- `prompt`: ticket text + any available context (related files, linked issues)

Extract from response:
- `scale` (small / medium / large)
- `affectedLayers` → set `hasUIComponent = true` if "frontend" is present
- `adrRequired` — determines whether ADR is needed in Phase 2
- `confidence` — if "provisional", present `scopeDependencies` questions to user and wait for answers before continuing
- `questions` — if any, present to user and incorporate answers before continuing

**Register all flow steps using TaskCreate after scale determination:**
- Phase 1: Requirements Analysis
- Phase 2: Design (technical-designer + document-reviewer)
- Phase 3: Sprint Plan + User Approval Gate
- Phase 4: Implementation (task-decomposer + per-task cycle)
- Phase 5: Code Review
- Phase 6: UI QA (if `hasUIComponent`)
- Phase 7: Pull Request

---

## Phase 2 — Design

### 2a. Technical Design

Invoke technical-designer:
- `subagent_type`: "dev:technical-designer"
- `prompt`: ticket text, requirement-analyzer output (scale, affectedFiles, constraints, adrRequired)

Extract `designDocPath` from response.

### 2b. Design Validation

Invoke document-reviewer:
- `subagent_type`: "dev:document-reviewer"
- `prompt`: `designDocPath`

If response status is `needs_revision`:
- Re-invoke technical-designer with the revision feedback
- Re-invoke document-reviewer
- Repeat until status is `approved` or escalate to user after 2 failed attempts

---

## Phase 3 — Sprint Plan Proposal [STOP: User Approval Required]

Invoke work-planner:
- `subagent_type`: "dev:work-planner"
- `prompt`: `designDocPath`

Extract `workPlanPath` from response.

**[Stop — Present sprint plan to user]**

Read the work plan and summarize:
- Scale and estimated phases
- Key tasks per phase
- Any E2E gaps or risks flagged by work-planner

Use AskUserQuestion to get approval:
- **Approve** → Proceed to Phase 4
- **Reject** → Ask for feedback, then restart from Phase 1 with: original ticket + previous work plan path + rejection feedback

On rejection restart:
- Pass all three to requirement-analyzer as `requirements` + `context`
- Re-run Phase 2 and Phase 3 with updated outputs

---

## Phase 4 — Implementation

### 4a. Task Decomposition

Invoke task-decomposer:
- `subagent_type`: "dev:task-decomposer"
- `prompt`: `workPlanPath`

Extract list of task file paths.

### 4b. Per-Task Execution Cycle

For each task file (complete each before starting the next):

1. **Invoke task-executor** (`subagent_type`: "dev:task-executor") — pass task file path
2. **Check task-executor response**:
   - `status: escalation_needed` or `blocked` → escalate to user
   - `requiresTestReview: true` → invoke integration-test-reviewer (`subagent_type`: "qa-workflows:integration-test-reviewer")
     - `needs_revision` → return to step 1 with `requiredFixes`
     - `approved` → continue to step 3
   - Otherwise → continue to step 3
3. **Invoke quality-fixer** (`subagent_type`: "dev:quality-fixer")
   - `stub_detected` → return to step 1 with `incompleteImplementations[]`
   - `blocked` → escalate to user
   - `approved` → continue to step 4
4. **git commit** via Bash

**MANDATORY suffix for ALL sub-agent prompts**:
```
[SYSTEM CONSTRAINT]
This agent operates within dev:prepare skill scope. Use orchestrator-provided rules only.
```

---

## Phase 5 — Code Review

Invoke code-reviewer:
- `subagent_type`: "dev:code-reviewer"
- `prompt`: `designDocPath`, implementation files from `git diff --name-only main...HEAD`

If verdict is `needs-improvement` or `needs-redesign`:
- Consolidate all findings into a single fix task file
- Re-run task-executor → quality-fixer for the fixes
- Re-run code-reviewer
- Repeat until verdict is `pass` or escalate after 2 failed cycles

---

## Phase 6 — UI QA (Conditional)

**Execute only when `hasUIComponent: true`.**

If no target URL was provided in the ticket description, ask the user:
> "What is the URL of the running web app for UI QA? (e.g. http://localhost:3000)"

Invoke web-qa-reviewer:
- `subagent_type`: "qa-workflows:web-qa-reviewer"
- `prompt`: target URL, `designDocPath`

If web-qa-reviewer returns findings with severity `high` or `critical`:
- Present findings to user
- Ask whether to fix before PR (re-enter Phase 4 cycle) or note findings in PR description

---

## Phase 7 — Pull Request

Invoke pr-creator:
- `subagent_type`: "dev:pr-creator"
- `prompt`: `designDocPath`, any QA findings to include in PR body

Extract `prUrl` and `prNumber` from response.

---

## Completion Report

Present to user:
- PR URL
- Scale and phases completed
- Work plan path (for reference)
- Any noted QA findings included in PR description
