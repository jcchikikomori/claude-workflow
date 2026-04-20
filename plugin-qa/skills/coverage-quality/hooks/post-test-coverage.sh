#!/usr/bin/env bash
# PostToolUse hook — auto-sniffs coverage after test runner commands.
# Fires after every Bash call; exits 0 silently when not a test command.
# Never blocks Claude — all errors are suppressed.

set -euo pipefail 2>/dev/null || true

COMMAND=$(echo "${CLAUDE_TOOL_INPUT:-}" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('command', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

# Only proceed for test runner commands
if ! echo "$COMMAND" | grep -qE '(rspec|pytest|jest|vitest|go test|mvn test|bundle exec rspec)'; then
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)"
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "")

# Stack detection (priority order matches SKILL.md)
if [ -f "pom.xml" ]; then
    STACK="java-maven"
elif [ -f "go.mod" ]; then
    STACK="go"
elif [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "Pipfile" ]; then
    STACK="python"
elif [ -f "Gemfile" ]; then
    STACK="ruby"
elif [ -f "package.json" ] && grep -q '"vitest"' package.json 2>/dev/null; then
    STACK="vitest"
elif [ -f "package.json" ] && grep -q '"jest"' package.json 2>/dev/null; then
    STACK="jest"
else
    exit 0
fi

mkdir -p .coverage-snapshot

# Parse coverage — silent on failure (coverage file may not exist yet if tests failed)
python3 "$SCRIPT_DIR/parse_coverage.py" \
    --stack "$STACK" \
    --commit "$COMMIT" \
    --output ".coverage-snapshot/latest.json" 2>/dev/null || exit 0

# Surface warning immediately if coverage is vacuous (e.g. empty SimpleCov result)
WARNING=$(python3 -c "
import json
try:
    print(json.load(open('.coverage-snapshot/latest.json')).get('warning', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

if [ "$WARNING" = "empty_coverage" ]; then
    echo "[coverage-quality] ⚠️  0 lines tracked — SimpleCov may be excluding source files. Run full suite for real coverage."
    exit 0
fi

# Compare vs baseline if one exists
if [ -f ".coverage-snapshot/baseline.json" ]; then
    BASELINE_COMMIT=$(python3 -c "
import json
try:
    print(json.load(open('.coverage-snapshot/baseline.json')).get('commit', 'HEAD~1'))
except Exception:
    print('HEAD~1')
" 2>/dev/null || echo "HEAD~1")

    CHANGED=$(git diff --name-only "${BASELINE_COMMIT}..HEAD" 2>/dev/null | tr '\n' ' ' || echo "")

    python3 "$SCRIPT_DIR/compare_coverage.py" \
        --baseline ".coverage-snapshot/baseline.json" \
        --current ".coverage-snapshot/latest.json" \
        --changed-files "$CHANGED" \
        --mode diff-check \
        --output ".coverage-snapshot/latest-delta.json" 2>/dev/null || exit 0

    python3 -c "
import json, sys
try:
    d = json.load(open('.coverage-snapshot/latest-delta.json'))
    ov = d['overall']
    sign = '+' if ov['delta'] >= 0 else ''
    print(f\"[coverage-quality] {ov['baseline_pct']}% → {ov['current_pct']}% ({sign}{ov['delta']}%) {ov['emoji']} {ov['status']}\")
except Exception:
    pass
" 2>/dev/null || true
else
    python3 -c "
import json, sys
try:
    d = json.load(open('.coverage-snapshot/latest.json'))
    ov = d['overall']
    print(f\"[coverage-quality] Current: {ov['percent']}% ({ov['lines_hit']}/{ov['lines_total']} lines). No baseline set — run /coverage-quality to set one.\")
except Exception:
    pass
" 2>/dev/null || true
fi
