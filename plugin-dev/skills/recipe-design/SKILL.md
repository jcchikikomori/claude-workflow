---
name: recipe-design
description: Execute from requirement analysis to design document creation
disable-model-invocation: true
---

**Context**: Dedicated to the design phase.

## Layer Detection

After requirement-analyzer runs, check `affectedLayers` from its output:

- Contains `frontend` → activate **frontend path** (use `technical-designer-frontend`, add UI Spec phase, add prototype inquiry)
- Backend only or unknown → activate **backend path** (use `technical-designer`)

## Orchestrator Definition

**Core Identity**: "I am an orchestrator." (see subagents-orchestration-guide skill)

**Execution Protocol**:

1. **Delegate all work** to sub-agents — your role is to invoke sub-agents, pass data between them, and report results
2. **Follow subagents-orchestration-guide skill design flow exactly**:
   - **Stop at every `[Stop: ...]` marker** → Wait for user approval before proceeding
3. **Scope**: Complete when design documents receive approval

**CRITICAL**: Execute document-reviewer, design-sync, and all stopping points — each serves as a quality gate.

## Workflow Overview

**Backend path:**

```
Requirements → requirement-analyzer → [Stop: Scale determination]
                                           ↓
                                   codebase-analyzer → technical-designer
                                           ↓
                                   code-verifier → document-reviewer
                                           ↓
                                      design-sync → [Stop: Design approval]
```

**Frontend path:**

```
Requirements → requirement-analyzer → [Stop: Scale determination]
                                           ↓
                    codebase-analyzer → ui-spec-designer → [Stop: UI Spec approval]
                                           ↓
                                   technical-designer-frontend
                                           ↓
                                   code-verifier → document-reviewer
                                           ↓
                                      design-sync → [Stop: Design approval]
```

## Scope Boundaries

**Included in this skill**:

- Requirement analysis with requirement-analyzer
- Codebase analysis with codebase-analyzer (before technical design)
- UI Specification creation with ui-spec-designer (frontend path only)
- ADR creation (if architecture changes, new technology, or data flow changes)
- Design Doc creation with technical-designer or technical-designer-frontend
- Design Doc verification with code-verifier (before document review)
- Document review with document-reviewer
- Design Doc consistency verification with design-sync

**Responsibility Boundary**: Completes with design document approval. Work planning is outside scope.

Requirements: $ARGUMENTS

## Execution Flow

### Step 1: Requirement Analysis

First engage in dialogue to understand requirements:

- What problems do you want to solve?
- Expected outcomes and success criteria
- Relationship with existing systems

Once user answers, invoke requirement-analyzer:

- `subagent_type`: "dev:requirement-analyzer"
- `prompt`: requirements text + any context
- **[STOP]**: Review results, address `questions` and `scopeDependencies`

Determine `affectedLayers` → set execution path (backend or frontend).

### Step 2: Codebase Analysis

Invoke codebase-analyzer:

- `subagent_type`: "dev:codebase-analyzer"
- `prompt`: requirement-analyzer JSON output + requirements text
- Follow subagents-orchestration-guide Call Examples

### Step 3: UI Specification (Frontend path only)

Ask the user: "Do you have prototype code for this feature? If so, provide the path — it will be placed in `docs/ui-spec/assets/` as reference material."

- **[STOP]**: Wait for user response

Invoke ui-spec-designer:

- `subagent_type`: "dev:ui-spec-designer"
- If PRD exists and prototype provided: `prompt`: "Create UI Spec from PRD at [path]. Prototype code at [path]."
- If PRD exists, no prototype: `prompt`: "Create UI Spec from PRD at [path]. No prototype available."
- If no PRD: `prompt`: "Create UI Spec from requirements: [requirement-analyzer output]."

Invoke document-reviewer on UI Spec, then **[STOP]** for user approval.

### Step 4: Design Document Creation

Present at least two design alternatives with trade-offs for each.

**Backend path** — invoke technical-designer:

- `subagent_type`: "dev:technical-designer"
- `prompt`: requirements, codebase-analyzer output, scale, adrRequired

**Frontend path** — invoke technical-designer-frontend:

- `subagent_type`: "dev:technical-designer-frontend"
- `prompt`: requirements, codebase-analyzer output, UI Spec path, scale, adrRequired

### Step 5: Verification and Review

- **(Design Doc only)** Invoke code-verifier: `subagent_type`: "dev:code-verifier", `doc_type: design-doc`, Design Doc path. Skip for ADR-only.
- Invoke document-reviewer: pass code-verifier results for Design Doc; omit for ADR.
- Invoke design-sync: `subagent_type`: "dev:design-sync", check all docs in `docs/design/`
- **[STOP]**: Present documents and design-sync results, obtain user approval

## Completion Criteria

- [ ] Executed requirement-analyzer and determined scale + layer
- [ ] Executed codebase-analyzer and passed results to technical designer
- [ ] (Frontend) Created UI Specification with ui-spec-designer and obtained approval
- [ ] Created appropriate design document (ADR or Design Doc) with layer-appropriate technical-designer
- [ ] Executed code-verifier on Design Doc and passed results to document-reviewer (skip for ADR-only)
- [ ] Executed document-reviewer and addressed feedback
- [ ] Executed design-sync for consistency verification
- [ ] Obtained user approval for design document

## Output Example

```
Design phase completed.
- UI Specification: docs/ui-spec/[feature]-ui-spec.md (frontend only)
- Design document: docs/design/[document-name].md or docs/adr/[document-name].md
- Approval status: User approved
```
