---
name: recipe-generate-claude-md
description: Generates a CLAUDE.md from scratch for a project that does not have one. Analyzes the codebase, produces instructions tailored for an AI coding agent, and optionally reviews the result. Use when starting work on a project with no CLAUDE.md.
disable-model-invocation: true
---

**Context**: CLAUDE.md generation workflow for projects that have no existing AI instruction file.

## Orchestrator Definition

**Core Identity**: "I am an orchestrator."

**First Action**: Register Steps 1-4 using TaskCreate before any execution.

**Why Delegate**: Codebase analysis and document generation each require full context. Delegating to subagents keeps each step focused and prevents context exhaustion in the orchestrator.

**Execution Method**:

- Codebase analysis → delegate to codebase-analyzer
- CLAUDE.md generation → delegate to claude-md-generator
- Document review → delegate to document-reviewer

Arguments: $ARGUMENTS
(Format: `[project_root]` — defaults to current working directory if omitted)

## Prerequisites

- Project root must exist and be accessible
- No existing CLAUDE.md at the target path (the generator will stop if one exists)

## Execution Flow

### Step 1: Resolve Project Root

If `$ARGUMENTS` is provided, use it as `$PROJECT_ROOT`. Otherwise, resolve with:

```bash
pwd
```

Verify the directory exists:

```bash
ls "$PROJECT_ROOT"
```

Stop if directory does not exist.

### Step 2: Codebase Analysis

Invoke codebase-analyzer using Agent tool:

- `subagent_type`: "dev:codebase-analyzer"
- `description`: "Analyze project for CLAUDE.md generation"
- `prompt`: |
  Analyze the codebase at [PROJECT_ROOT] for CLAUDE.md generation purposes.
  requirements: "Generate CLAUDE.md — understand the project's stack, build commands, test commands, lint setup, code conventions, Docker usage, and database practices."
  focus_areas: "build commands, test commands, lint/format configuration, code style conventions, Docker setup, database setup, environment variables"

Store output as `$STEP_2_OUTPUT`.

### Step 3: Generate CLAUDE.md

Invoke claude-md-generator using Agent tool:

- `subagent_type`: "dev:claude-md-generator"
- `description`: "Generate CLAUDE.md"
- `prompt`: |
  Generate CLAUDE.md for the project at [PROJECT_ROOT].
  project_root: [PROJECT_ROOT]
  codebase_analysis: [full $STEP_2_OUTPUT]

Store output as `$STEP_3_OUTPUT`.

Check response:

- `status: "blocked"` → Stop. Report reason to user (likely CLAUDE.md already exists).
- `status: "completed"` → Proceed to Step 4.

### Step 4: Review Generated CLAUDE.md

Invoke document-reviewer using Agent tool:

- `subagent_type`: "dev:document-reviewer"
- `description`: "Review generated CLAUDE.md"
- `prompt`: |
  Review the generated CLAUDE.md at [PROJECT_ROOT]/CLAUDE.md.
  Verify it is: concise (60-150 lines), specific to this project (no generic advice), accurate (commands match what was discovered), and free of sections with nothing meaningful.
  Provide approval or list specific improvements needed.

Check response:

- `approved` → Present completion message to user.
- `needs_revision` → Apply reviewer's required fixes to CLAUDE.md directly (orchestrator edits the file), then present completion message.

### Completion Message

```
CLAUDE.md generated at [PROJECT_ROOT]/CLAUDE.md
- Stack detected: [stackDetected from Step 3]
- Sections: [sectionsGenerated from Step 3]
[If reviewer requested fixes: "- Applied [n] reviewer suggestions"]
[If notes from generator: "- Note: [notes]"]

Run /reload-plugins to apply if this is a Claude Code plugin project.
```
