---
name: recipe-web-qa
description: Browser-layer QA workflow for a live running web application. Inspects a URL using Chrome DevTools, classifies findings by severity, generates test skeletons for critical/high issues, and produces a QA report. Use when QA validation of a running web app is needed.
disable-model-invocation: true
---

**Context**: QA inspection workflow for a live web application using Chrome DevTools browser tools.

## Orchestrator Definition

**Core Identity**: "I am an orchestrator."

**First Action**: Register Steps 1-5 using TaskCreate before any execution.

**Why Delegate**: Browser inspection, test skeleton generation, and report assembly each require focused context. Subagents work in isolated context; the orchestrator bridges structured JSON between them.

**Execution Method**:

- URL validation → orchestrator runs directly (Bash)
- Browser inspection → delegate to web-qa-reviewer
- Test skeleton generation → delegate to acceptance-test-generator (when Design Doc provided and critical/high findings exist)
- QA report → orchestrator assembles from subagent outputs

Arguments: $ARGUMENTS
(Format: `<url> [Design Doc path]`)

## Execution Flow

### Step 1: Validate Inputs

Parse `$ARGUMENTS`:

- First token → `$URL`
- Second token (optional) → `$DESIGN_DOC`

```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$URL"
```

- HTTP 200–399 → proceed
- Any other result → stop: "URL not reachable: [URL]. Received [status]. Verify the application is running."

If `$DESIGN_DOC` provided:

```bash
ls "$DESIGN_DOC"
```

- File exists → proceed with Design Doc context
- File missing → warn user ("Design Doc not found at [path]. Proceeding without scope context.") and continue

### Step 2: Browser Inspection

Invoke web-qa-reviewer using Agent tool:

- `subagent_type`: "dev-workflows:web-qa-reviewer"
- `description`: "Browser QA inspection"
- `prompt`: "Inspect the following URL and return structured findings. URL: [URL from Step 1]. Scope: [Design Doc path if provided, otherwise omit]"

Store output as `$STEP_2_OUTPUT`.

Check response:

- `status: "blocked"` → Stop. Report `blockedReason` to user and exit.
- `status: "completed"` → Proceed to Step 3.

### Step 3: Classify Findings and Determine Next Action

From `$STEP_2_OUTPUT.findings`, partition by severity:

- `critical_and_high` = findings where severity is `critical` or `high`
- `medium_and_low` = remaining findings

Decision table:

| critical/high findings | Design Doc provided | Action |
| ---------------------- | ------------------- | ------ |
| Yes | Yes | Step 4A |
| Yes | No | Step 4B |
| No | Either | Skip to Step 5 |

### Step 4A: Generate Test Skeletons from Design Doc

Invoke acceptance-test-generator using Agent tool:

- `subagent_type`: "dev-workflows:acceptance-test-generator"
- `description`: "Generate test skeletons for QA findings"
- `prompt`: "Generate test skeletons targeting the following critical/high QA findings. Design Doc: [Design Doc path]. Focus on ACs related to these findings: [list descriptions from critical_and_high]"

Store output as `$STEP_4_OUTPUT` (contains `generatedFiles`).

### Step 4B: Create Manual Test Skeletons

Create `docs/qa/web-qa-skeletons-YYYYMMDD.md` with one entry per critical/high finding:

```markdown
## [finding.description]

- Severity: [severity]
- Category: [category]
- Evidence: [evidence]
- Verification: [steps to reproduce and confirm the issue is resolved]
- Pass Criteria: [observable condition that confirms fix]
```

Store as `$STEP_4_OUTPUT = { "generatedFiles": { "manual": "docs/qa/web-qa-skeletons-YYYYMMDD.md" } }`.

### Step 5: Generate QA Report

Write `docs/qa/web-qa-report-YYYYMMDD.md` using the following structure:

```markdown
# Web QA Report — [URL]

Generated: [date]

## Summary

| Severity | Count |
| -------- | ----- |
| Critical | [n] |
| High | [n] |
| Medium | [n] |
| Low | [n] |
| **Total** | [n] |

## Lighthouse Scores

| Category | Score | Status |
| -------- | ----- | ------ |
| Performance | [score] | pass/fail |
| Accessibility | [score] | pass/fail |
| Best Practices | [score] | pass/fail |
| SEO | [score] | pass/fail |

## Critical Findings

[For each critical finding: ### [description] + Category + Evidence]

## High Findings

[For each high finding: ### [description] + Category + Evidence]

## Medium / Low Findings

[Bullet list: "- [description] ([category])"]

## Test Gaps

[If skeletons generated:]
Skeleton file: [path from $STEP_4_OUTPUT]
Covers [n] critical/high findings.

[If no skeletons generated:]
No critical/high findings requiring test coverage.

## Screenshot

[screenshotNote from web-qa-reviewer output]
```

Present the result to the user:

```
Web QA inspection complete.
- Report: docs/qa/web-qa-report-YYYYMMDD.md
- Critical: [n] | High: [n] | Medium: [n] | Low: [n]
- Test skeletons: [path] (if generated)
```
