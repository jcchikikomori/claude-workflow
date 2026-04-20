---
name: coverage-quality
description: Local SonarQube-style coverage quality tool. Detects tech stack, runs test coverage, stores a baseline snapshot, and compares coverage vs baseline to show degraded/improved/missing coverage per file and line. Use this skill whenever someone asks about coverage quality, test coverage degradation, coverage baseline, coverage delta after code changes, missing lines, or wants a local code quality report like SonarQube or CI coverage reports. Also use when the user asks "did I break coverage?" or "show coverage diff".
---

# Coverage Quality

## References

- Stack detection, commands, parse approach: [references/stacks.md](references/stacks.md)
- Report templates and severity rules: [references/report-format.md](references/report-format.md)

---

## Architecture

Two layers work together:

**Hook (passive)** — `hooks/post-test-coverage.sh` fires automatically after every test run via `PostToolUse`. It sniffs the Bash command for test runner keywords (`rspec`, `pytest`, `jest`, `vitest`, `go test`, `mvn test`), parses the coverage output, and writes:
- `.coverage-snapshot/latest.json` — current unified coverage
- `.coverage-snapshot/latest-delta.json` — comparison vs baseline (if baseline exists)
- Prints a 1-line summary into Claude context

**Skill (on-demand)** — reads pre-computed delta (fast path) or re-runs coverage (fallback), then renders the full terminal report.

---

## Invocation Modes

| Trigger phrase | Mode |
|----------------|------|
| "check coverage", "coverage quality", no baseline | **first-run** |
| "coverage degraded?", "diff check", "since last baseline" | **diff-check** |
| "full coverage report", "all files" | **full-report** |
| "update baseline", "set baseline" | **update** |

---

## Execution Flow

### Step 1: Detect Stack

Read detection rules from `references/stacks.md`. Check project root in priority order:

```bash
ls pom.xml go.mod pyproject.toml setup.py Pipfile Gemfile package.json 2>/dev/null
```

For `package.json`, check for `vitest` (higher priority) then `jest`:
```bash
grep -E '"(vitest|jest)"' package.json
```

If no supported file found, stop:
> "Could not detect project stack. Supported: Python, Ruby, JS (Jest/Vitest), Java (Maven), Go."

### Step 2: Check for Fresh Pre-Computed Data

If `.coverage-snapshot/latest-delta.json` exists and its `current_commit` matches HEAD — skip Steps 3–4, go straight to Step 5.

```bash
git rev-parse --short HEAD
```

### Step 3: Run Coverage (if no fresh data)

Show the command before running it. Consult `references/stacks.md` for the exact command per stack.

If the command fails, stop with the tool error output:
> "Coverage run failed. Fix test failures before running coverage-quality."

### Step 4: Parse to Unified JSON

```bash
python3 <skill-path>/scripts/parse_coverage.py \
  --stack <detected-stack> \
  --commit "$(git rev-parse --short HEAD)" \
  --output .coverage-snapshot/latest.json
```

`<skill-path>` is the absolute path to this skill's directory.

### Step 5: Check Baseline

```bash
ls .coverage-snapshot/baseline.json 2>/dev/null || echo "NO_BASELINE"
```

- No baseline + not `update` mode → treat as **first-run**

### Step 6: Compare (skip on first-run)

Get changed files since baseline commit:

```bash
BASELINE_COMMIT=$(python3 -c "import json; print(json.load(open('.coverage-snapshot/baseline.json')).get('commit','HEAD~1'))")
git diff --name-only "${BASELINE_COMMIT}..HEAD"
```

```bash
python3 <skill-path>/scripts/compare_coverage.py \
  --baseline .coverage-snapshot/baseline.json \
  --current .coverage-snapshot/latest.json \
  --changed-files "<space-separated paths from git diff>" \
  --mode <diff-check|full-report> \
  --output .coverage-snapshot/latest-delta.json
```

### Step 7: Save / Update Baseline

On **first-run** or **update** mode:

```bash
mkdir -p .coverage-snapshot
cp .coverage-snapshot/latest.json .coverage-snapshot/baseline.json
```

Add to `.gitignore` if not present:
```bash
grep -q '\.coverage-snapshot' .gitignore 2>/dev/null || echo '.coverage-snapshot/' >> .gitignore
```

### Step 8: Render Report

Read the delta JSON (or `latest.json` on first-run) and format using the templates in `references/report-format.md`. Apply column alignment so all `→` symbols line up vertically.

---

## Threshold Configuration

Default: **80%**. Override via `.coverage-snapshot/config.json`:
```json
{ "threshold": 75 }
```

---

## Hook Setup Instructions

To enable passive coverage tracking on every test run, register the hook in Claude Code settings.

Find the absolute path to this skill's hooks directory:
```bash
find ~/.claude/plugins -name "post-test-coverage.sh" 2>/dev/null
```

Then add to `.claude/settings.json` (project-level) or `~/.claude/settings.json` (global):
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"/path/to/coverage-quality/hooks/post-test-coverage.sh\""
          }
        ]
      }
    ]
  }
}
```

Replace `/path/to/coverage-quality/` with the actual path from the `find` command above.

After setup: every time tests run, a 1-line coverage summary appears automatically in Claude context. Ask "show me the coverage report" to expand the full detail.

---

## Gitignore Safety

Always ensure `.coverage-snapshot/` is in `.gitignore`. Never commit baseline snapshots — they contain local file paths and are machine-specific.

---

## Error Reference

| Situation | Behavior |
|-----------|----------|
| Stack not detected | Stop with clear message listing supported stacks |
| Coverage command fails | Stop with tool error output |
| Parser script missing | Stop: "Parser script missing. Reinstall the qa plugin." |
| No baseline + comparison requested | Continue as first-run, inform user |
| Baseline commit not in git history | Continue with full file list, warn user to update baseline |
| Ruby: 0 lines tracked (vacuous 100%) | Show `warning_hints` prominently. Suggest running full suite: `bundle exec rspec spec/` |
