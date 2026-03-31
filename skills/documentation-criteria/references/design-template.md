# [Feature Name] Design Document

## Overview

[Explain the purpose and overview of this feature in 2-3 sentences]

### Referenced UI Spec (when feature includes frontend)
- UI Spec path: [docs/ui-spec/xxx-ui-spec.md]
- Component structure and state design are inherited from UI Spec

## Design Summary (Meta)

```yaml
design_type: "new_feature|extension|refactoring"
risk_level: "low|medium|high"
complexity_level: "low|medium|high"
complexity_rationale: "[Required if medium/high: (1) which requirements/ACs necessitate this complexity, (2) which constraints/risks it addresses]"
main_constraints:
  - "[constraint 1]"
  - "[constraint 2]"
biggest_risks:
  - "[risk 1]"
  - "[risk 2]"
unknowns:
  - "[uncertainty 1]"
  - "[uncertainty 2]"
```

## Background and Context

### Prerequisite ADRs

- [ADR File Name]: [Related decision items]
- Reference common technical ADRs when applicable

### Agreement Checklist

#### Scope
- [ ] [Features/components to change]
- [ ] [Features to add]

#### Non-Scope (Explicitly not changing)
- [ ] [Features/components not to change]
- [ ] [Existing logic to preserve]

#### Constraints
- [ ] Parallel operation: [Yes/No]
- [ ] Backward compatibility: [Required/Not required]
- [ ] Performance measurement: [Required/Not required]

#### Applicable Standards
- [ ] [Standard/convention] `[explicit]` - Source: [config / rule file / documentation path]
- [ ] [Observed pattern] `[implicit]` - Evidence: [file paths] - Confirmed: [Yes/No]

### Problem to Solve

[Specific problems or challenges this feature aims to address]

### Current Challenges

[Current system issues or limitations]

### Requirements

#### Functional Requirements

- [List mandatory functional requirements]

#### Non-Functional Requirements

- **Performance**: [Response time, throughput requirements]
- **Scalability**: [Requirements for handling increased load]
- **Reliability**: [Error rate, availability requirements]
- **Maintainability**: [Code readability and changeability]

## Acceptance Criteria (AC) - EARS Format

Each AC is written in EARS (Easy Approach to Requirements Syntax) format.
Keywords determine test type and reduce ambiguity.

**EARS Keywords**:
| Keyword | Usage | Test Type |
|---------|-------|-----------|
| **When** | Event-triggered behavior | Event-driven test |
| **While** | State-dependent behavior | State condition test |
| **If-then** | Conditional behavior | Branch coverage test |
| (none) | Ubiquitous behavior | Basic functionality test |

**Format**: `[Keyword] <trigger/condition>, the system shall <expected behavior>`

### [Functional Requirement 1]

- [ ] **When** user clicks login button with valid credentials, the system shall authenticate and redirect to dashboard
- [ ] **If** credentials are invalid, **then** the system shall display error message "Invalid credentials"
- [ ] **While** user is logged in, the system shall maintain the session for configured timeout period

### [Functional Requirement 2]

- [ ] The system shall display data list with pagination of 10 items per page
- [ ] **When** input is entered in search field, the system shall apply real-time filtering

## Existing Codebase Analysis

### Implementation Path Mapping
| Type | Path | Description |
|------|------|-------------|
| Existing | src/[actual-path] | [Current implementation] |
| New | src/[planned-path] | [Planned new creation] |

### Integration Points (Include even for new implementations)
- **Integration Target**: [What to connect with]
- **Invocation Method**: [How it will be invoked]

### Code Inspection Evidence

| File/Function | Relevance |
|---------------|-----------|
| [path:function] | [similar functionality / integration point / pattern reference] |

## Design

### Change Impact Map

```yaml
Change Target: [Component/feature to change]
Direct Impact:
  - [Files/functions requiring direct changes]
  - [Interface change points]
Indirect Impact:
  - [Data format changes]
  - [Processing time changes]
No Ripple Effect:
  - [Explicitly specify unaffected features]
```

### Architecture Overview

[How this feature is positioned within the overall system]

### Data Flow

```
[Express data flow using diagrams or pseudo-code]
```

### Integration Points List

| Integration Point | Location | Old Implementation | New Implementation | Switching Method |
|-------------------|----------|-------------------|-------------------|------------------|
| Integration Point 1 | [Class/Function] | [Existing Process] | [New Process] | [DI/Factory etc.] |
| Integration Point 2 | [Another Location] | [Existing] | [New] | [Method] |

### Main Components

#### Component 1

- **Responsibility**: [Scope of responsibility for this component]
- **Interface**: [APIs and contract definitions provided]
- **Dependencies**: [Relationships with other components]

#### Component 2

- **Responsibility**: [Scope of responsibility for this component]
- **Interface**: [APIs and contract definitions provided]
- **Dependencies**: [Relationships with other components]

### Data Representation Decision (When Introducing New Structures)

| Criterion | Assessment | Reason |
|-----------|-----------|--------|
| Semantic Fit | [Yes/No] | [Does existing structure's meaning align?] |
| Responsibility Fit | [Yes/No] | [Same bounded context?] |
| Lifecycle Fit | [Yes/No] | [Same creation/mutation/deletion timing?] |
| Boundary/Interop Cost | [Low/Medium/High] | [Cost of sharing across boundaries?] |

**Decision**: [reuse / extend / new] — [rationale in 1-2 sentences]

### Contract Definitions

```
// Record major contract/interface definitions here
```

### Data Contract

#### Component 1

```yaml
Input:
  Type: [Data shape, contract, or schema]
  Preconditions: [Required items, format constraints]
  Validation: [Validation method]

Output:
  Type: [Data shape, contract, or schema]
  Guarantees: [Conditions that must always be met]
  On Error: [Exception/null/default value]

Invariants:
  - [Conditions that remain unchanged before and after processing]
```

### Field Propagation Map (When Fields Cross Boundaries)

| Field | Boundary | Status | Detail |
|-------|----------|--------|--------|
| [field name] | [Component A → B] | preserved / transformed / dropped | [logic or reason] |

### State Transitions and Invariants (When Applicable)

```yaml
State Definition:
  - Initial State: [Initial values and conditions]
  - Possible States: [List of states]

State Transitions:
  Current State → Event → Next State

System Invariants:
  - [Conditions that hold in any state]
```

### UI Error State Design (when feature includes frontend)

| Component / Screen | Loading | Empty | Error | Partial |
|-------------------|---------|-------|-------|---------|
| [Component name] | [Skeleton / spinner] | [Empty state + CTA] | [Error message + Retry] | [Cached display + Banner] |

### Client State Design (when feature includes frontend)

| State Category | State | Management Method | Sync Strategy |
|---------------|-------|-------------------|---------------|
| Server state | [Fetched data] | [Cache library / custom hook] | [Polling / WebSocket / manual refresh] |
| Local UI state | [Modal open, tab selection] | [useState / useReducer] | - |
| Temporary state | [Form input, draft] | [useState / form library] | [Auto-save / manual save] |

### UI Action - API Contract Mapping (when feature includes frontend)

| UI Action | API Endpoint | Request | Response | Error Contract |
|-----------|-------------|---------|----------|----------------|
| [Button click / form submit] | [POST /api/xxx] | [Request body fields] | [Response fields] | [Error codes and UI handling] |

### Error Handling

[Types of errors and how to handle them]

### Logging and Monitoring

[What to record in logs and how to monitor]

## Implementation Plan

### Implementation Approach

**Selected Approach**: [Approach name or combination]
**Selection Reason**: [Reason considering project constraints and technical dependencies]

### Technical Dependencies and Implementation Order

#### Required Implementation Order
1. **[Component/Feature A]**
   - Technical Reason: [Why this needs to be implemented first]
   - Dependent Elements: [Other components that depend on this]

2. **[Component/Feature B]**
   - Technical Reason: [Technical necessity to implement after A]
   - Prerequisites: [Required pre-implementations]

### Integration Points

**Integration Point 1: [Name]**
- Components: [Component A] → [Component B]
- Contract: [Interface/API contract between components]

**Integration Point 2: [Name]**
- Components: [Component B] → [Component C]
- Contract: [Interface/API contract between components]

### Migration Strategy

[Technical migration approach, ensuring backward compatibility]

## Security Considerations

Evaluate the following for this feature's trust boundaries and data flow:

- **Authentication & Authorization**: What authentication is required for new entry points? What authorization checks protect resource access?
- **Input Validation**: Where does external input enter the system? How is it validated before processing?
- **Sensitive Data Handling**: What data requires protection (encryption, masking, access control)? What data is safe to include in logs and error responses?

Mark items as N/A with brief rationale when the feature has no relevant trust boundary.

## Test Boundaries

### Mock Boundary Decisions

| Component/Dependency | Mock? | Rationale |
|---------------------|-------|-----------|
| [External API / DB / File system / etc.] | [Yes/No] | [Why this boundary was chosen] |

### Data Layer Testing Strategy

- **Schema dependencies**: [List tables/models this feature reads from or writes to, with paths to their definitions]
- **Test data approach**: [How test data is provided — fixtures, factories, seed scripts, or real database]
- **Mock limitations acknowledged**: [What cannot be reliably tested with mocks alone for this feature]

Mark as N/A with brief rationale when the feature has no data layer dependencies.

### Integration Verification Points

- [List critical integration points that require testing beyond unit-level mocks]

## Future Extensibility

[Considerations for future feature additions or changes]

## Alternative Solutions

### Alternative 1

- **Overview**: [Description of alternative solution]
- **Advantages**: [Advantages]
- **Disadvantages**: [Disadvantages]
- **Reason for Rejection**: [Why it wasn't adopted]

## Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| [Risk 1] | High/Medium/Low | High/Medium/Low | [Countermeasure] |

## References

- [Related documentation and links]

## Update History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| YYYY-MM-DD | 1.0 | Initial version | [Name] |
