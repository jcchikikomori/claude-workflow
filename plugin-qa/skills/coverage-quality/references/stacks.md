# Coverage Stacks Reference

## Stack Detection Priority

| Priority | Stack | Detection Files |
|----------|-------|----------------|
| 1 | java-maven | `pom.xml` |
| 2 | go | `go.mod` |
| 3 | python | `pyproject.toml` OR `setup.py` OR `Pipfile` |
| 4 | ruby | `Gemfile` |
| 5 | vitest | `package.json` containing `"vitest"` in dependencies |
| 6 | jest | `package.json` containing `"jest"` in dependencies |

Detection precedence matters when multiple files coexist (e.g. a Rails app with a `package.json` for its asset pipeline — detect Ruby, not JS).

---

## Per-Stack Details

### Python

**Detection**: Any of `pyproject.toml`, `setup.py`, `Pipfile` in project root.

**Prerequisites**: `pip install coverage pytest`

**Coverage command**:
```bash
coverage run -m pytest && coverage json
```

**Output file**: `coverage.json`

**Parse approach**:
- `files[path].summary.num_statements` → `lines_total`
- `files[path].summary.covered_lines` → `lines_hit`
- `files[path].summary.percent_covered` → `percent`
- `files[path].missing_lines` → `missing_lines`
- `totals.*` → overall

---

### Ruby / Rails

**Detection**: `Gemfile` in project root.

**Prerequisites**: `simplecov` gem in test group; `require 'simplecov'` at top of `spec_helper.rb`.

**Coverage command**:
```bash
COVERAGE=true bundle exec rspec
```

**Output file**: `coverage/.resultset.json`

**Parse approach**:
- Take first key (e.g. `"RSpec"`) as result group
- `coverage[path].lines` — array where `null` = not executable, `0` = uncovered, `>0` = covered
- `lines_total` = count of non-null entries
- `lines_hit` = count of entries > 0
- `missing_lines` = 1-indexed positions where entry == 0

---

### JavaScript — Jest

**Detection**: `package.json` with `"jest"` in dependencies.

**Coverage command**:
```bash
jest --coverage --coverageReporters=json
```

**Output file**: `coverage/coverage-final.json`

**Parse approach** (Istanbul V8 format):
- `s` = statement hit counts, `statementMap` = line positions
- `lines_total` = count of entries in `s`
- `lines_hit` = count where `s[key] > 0`
- `missing_lines` = start lines from `statementMap` entries where `s[key] == 0`

---

### JavaScript — Vitest

**Detection**: `package.json` with `"vitest"` in dependencies (checked before jest).

**Prerequisites**: `@vitest/coverage-v8` or `@vitest/coverage-istanbul` installed.

**Coverage command**:
```bash
vitest run --coverage --reporter=json
```

**Output file**: `coverage/coverage.json`

**Parse approach**: Identical to Jest (same Istanbul-compatible JSON, different file path).

---

### Java — Maven / JaCoCo

**Detection**: `pom.xml` in project root.

**Prerequisites**: JaCoCo plugin in `pom.xml`:
```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <executions>
    <execution><goals><goal>prepare-agent</goal></goals></execution>
  </executions>
</plugin>
```

**Coverage command**:
```bash
mvn test jacoco:report
```

**Output file**: `target/site/jacoco/jacoco.xml`

### Common Issues — Ruby

**`local_gems/` not tracked**

SimpleCov's `'rails'` profile only instruments `app/`, `lib/`, `config/`. Projects with source under `local_gems/` need explicit config in `spec/rails_helper.rb` or `.simplecov`:

```ruby
SimpleCov.start 'rails' do
  add_group 'Local Gems', 'local_gems'
end
```

**Single-file filter producing empty coverage**

When one spec file is run, RSpec may add a filter keeping only the matching source file — which itself may be excluded by the SimpleCov profile. Result: `.resultset.json` has an empty `coverage` hash → parser reports `0/0 (100%)`.

Fix: run a directory or full suite:

```bash
bundle exec rspec spec/local_gems/portals_bff/
# or
bundle exec rspec spec/
```

Both issues produce `warning: "empty_coverage"` in the unified JSON. The skill and hook surface this prominently instead of reporting a misleading 100%.

---

**Parse approach** (XML via `xml.etree.ElementTree`):
- Each `<sourcefile>` in a `<package>`: path = `package/@name + "/" + sourcefile/@name`
- `<counter type="LINE">` attributes: `missed` + `covered` = `lines_total`
- `<line ci="0">` elements → `missing_lines` (attribute `nr`)
- Root-level `<counter type="LINE">` → overall totals

---

### Go

**Detection**: `go.mod` in project root.

**Coverage command**:
```bash
go test -coverprofile=coverage.out ./...
```

**Output file**: `coverage.out`

**Format**: `file:startLine.startCol,endLine.endCol numStmts count`

**Parse approach**:
- Skip first line (`mode: set/count/atomic`)
- Group records by file path; strip module prefix (from `go.mod`)
- `count > 0` → line covered; `count == 0` → uncovered
- `lines_total` = unique start lines per file

---

## Unified JSON Schema

All parsers output this schema:

```json
{
  "timestamp": "2026-04-20T12:00:00Z",
  "commit": "abc1234",
  "stack": "python",
  "overall": {
    "lines_total": 500,
    "lines_hit": 400,
    "percent": 80.0
  },
  "files": {
    "src/foo.py": {
      "lines_total": 50,
      "lines_hit": 45,
      "percent": 90.0,
      "missing_lines": [12, 34, 56]
    }
  }
}
```

`stack` is one of: `python`, `ruby`, `jest`, `vitest`, `java-maven`, `go`.
