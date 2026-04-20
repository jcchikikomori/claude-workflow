#!/usr/bin/env python3
"""
parse_coverage.py — Converts stack-specific coverage output to unified JSON.

Usage:
  python3 parse_coverage.py --stack <stack> --output <output.json> [--commit <sha>]

Supported stacks: python, ruby, jest, vitest, java-maven, go

Output schema:
  {
    "timestamp": "ISO8601",
    "commit": "sha or empty string",
    "stack": "python",
    "overall": {"lines_total": N, "lines_hit": N, "percent": N},
    "files": {
      "src/foo.py": {
        "lines_total": N, "lines_hit": N, "percent": N,
        "missing_lines": [N, ...]
      }
    }
  }
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def percent(hit: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(hit / total * 100, 2)


def build_unified(stack: str, commit: str, overall: dict, files: dict) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "stack": stack,
        "overall": overall,
        "files": files,
    }


def parse_python(commit: str) -> dict:
    path = "coverage.json"
    if not os.path.exists(path):
        sys.exit(f"ERROR: {path} not found. Run 'coverage run -m pytest && coverage json' first.")

    with open(path) as f:
        data = json.load(f)

    files = {}
    for filepath, info in data.get("files", {}).items():
        summary = info.get("summary", {})
        total = summary.get("num_statements", 0)
        hit = summary.get("covered_lines", 0)
        missing = sorted(info.get("missing_lines", []))
        files[filepath] = {
            "lines_total": total,
            "lines_hit": hit,
            "percent": percent(hit, total),
            "missing_lines": missing,
        }

    totals = data.get("totals", {})
    overall = {
        "lines_total": totals.get("num_statements", 0),
        "lines_hit": totals.get("covered_lines", 0),
        "percent": round(totals.get("percent_covered", 0.0), 2),
    }
    return build_unified("python", commit, overall, files)


def parse_ruby(commit: str) -> dict:
    path = "coverage/.resultset.json"
    if not os.path.exists(path):
        sys.exit(f"ERROR: {path} not found. Run 'COVERAGE=true bundle exec rspec' first.")

    with open(path) as f:
        data = json.load(f)

    suite_key = next(iter(data))
    coverage_data = data[suite_key].get("coverage", {})

    files = {}
    total_all, hit_all = 0, 0

    for filepath, info in coverage_data.items():
        lines = info.get("lines", []) if isinstance(info, dict) else info
        non_null = [l for l in lines if l is not None]
        total = len(non_null)
        hit = sum(1 for l in non_null if l > 0)
        missing = [i + 1 for i, l in enumerate(lines) if l == 0]

        files[filepath] = {
            "lines_total": total,
            "lines_hit": hit,
            "percent": percent(hit, total),
            "missing_lines": missing,
        }
        total_all += total
        hit_all += hit

    overall = {
        "lines_total": total_all,
        "lines_hit": hit_all,
        "percent": percent(hit_all, total_all),
    }
    result = build_unified("ruby", commit, overall, files)

    if total_all == 0:
        hints = []
        if os.path.isdir("local_gems"):
            hints.append(
                "local_gems/ dir found but not tracked — add "
                "`add_group 'Local Gems', 'local_gems'` to SimpleCov config"
            )
        hints.append(
            "single-file filter may be active — run full suite instead of one spec file"
        )
        result["warning"] = "empty_coverage"
        result["warning_hints"] = hints

    return result


def parse_istanbul(stack: str, commit: str) -> dict:
    path = "coverage/coverage-final.json" if stack == "jest" else "coverage/coverage.json"
    if not os.path.exists(path):
        cmd = ("jest --coverage --coverageReporters=json"
               if stack == "jest"
               else "vitest run --coverage --reporter=json")
        sys.exit(f"ERROR: {path} not found. Run '{cmd}' first.")

    with open(path) as f:
        data = json.load(f)

    files = {}
    total_all, hit_all = 0, 0

    for filepath, info in data.items():
        s = info.get("s", {})
        statement_map = info.get("statementMap", {})

        total = len(s)
        hit = sum(1 for v in s.values() if v > 0)

        missing_lines_set = set()
        for key, val in s.items():
            if val == 0 and key in statement_map:
                start_line = statement_map[key].get("start", {}).get("line")
                if start_line is not None:
                    missing_lines_set.add(start_line)
        missing = sorted(missing_lines_set)

        files[filepath] = {
            "lines_total": total,
            "lines_hit": hit,
            "percent": percent(hit, total),
            "missing_lines": missing,
        }
        total_all += total
        hit_all += hit

    overall = {
        "lines_total": total_all,
        "lines_hit": hit_all,
        "percent": percent(hit_all, total_all),
    }
    return build_unified(stack, commit, overall, files)


def parse_java_maven(commit: str) -> dict:
    import xml.etree.ElementTree as ET

    path = "target/site/jacoco/jacoco.xml"
    if not os.path.exists(path):
        sys.exit(f"ERROR: {path} not found. Run 'mvn test jacoco:report' first.")

    tree = ET.parse(path)
    root = tree.getroot()

    files = {}
    total_all, hit_all = 0, 0

    for package in root.findall("package"):
        pkg_name = package.get("name", "").replace("/", ".")
        for sourcefile in package.findall("sourcefile"):
            fname = sourcefile.get("name", "")
            filepath = f"{pkg_name}/{fname}" if pkg_name else fname

            missing = []
            for line in sourcefile.findall("line"):
                if int(line.get("ci", 0)) == 0:
                    missing.append(int(line.get("nr", 0)))

            counter = sourcefile.find("counter[@type='LINE']")
            if counter is None:
                continue
            missed = int(counter.get("missed", 0))
            covered = int(counter.get("covered", 0))
            total = missed + covered

            files[filepath] = {
                "lines_total": total,
                "lines_hit": covered,
                "percent": percent(covered, total),
                "missing_lines": sorted(missing),
            }
            total_all += total
            hit_all += covered

    root_counter = root.find("counter[@type='LINE']")
    if root_counter is not None:
        r_missed = int(root_counter.get("missed", 0))
        r_covered = int(root_counter.get("covered", 0))
        r_total = r_missed + r_covered
        overall = {
            "lines_total": r_total,
            "lines_hit": r_covered,
            "percent": percent(r_covered, r_total),
        }
    else:
        overall = {
            "lines_total": total_all,
            "lines_hit": hit_all,
            "percent": percent(hit_all, total_all),
        }

    return build_unified("java-maven", commit, overall, files)


def parse_go(commit: str) -> dict:
    path = "coverage.out"
    if not os.path.exists(path):
        sys.exit(f"ERROR: {path} not found. Run 'go test -coverprofile=coverage.out ./...' first.")

    module_name = ""
    if os.path.exists("go.mod"):
        with open("go.mod") as f:
            for line in f:
                if line.startswith("module "):
                    module_name = line.split()[1].strip()
                    break

    file_data: dict = {}

    with open(path) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if i == 0 or not line:
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            location = parts[0]
            count = int(parts[2])

            colon_idx = location.rfind(":")
            if colon_idx == -1:
                continue
            filepath = location[:colon_idx]
            coord_part = location[colon_idx + 1:]

            try:
                start_line = int(coord_part.split(",")[0].split(".")[0])
            except (ValueError, IndexError):
                continue

            if module_name and filepath.startswith(module_name + "/"):
                display_path = filepath[len(module_name) + 1:]
            else:
                display_path = filepath

            if display_path not in file_data:
                file_data[display_path] = {}

            existing = file_data[display_path].get(start_line, False)
            file_data[display_path][start_line] = existing or (count > 0)

    files = {}
    total_all, hit_all = 0, 0

    for filepath, line_map in file_data.items():
        total = len(line_map)
        hit = sum(1 for v in line_map.values() if v)
        missing = sorted(ln for ln, covered in line_map.items() if not covered)

        files[filepath] = {
            "lines_total": total,
            "lines_hit": hit,
            "percent": percent(hit, total),
            "missing_lines": missing,
        }
        total_all += total
        hit_all += hit

    overall = {
        "lines_total": total_all,
        "lines_hit": hit_all,
        "percent": percent(hit_all, total_all),
    }
    return build_unified("go", commit, overall, files)


PARSERS = {
    "python": parse_python,
    "ruby": parse_ruby,
    "jest": lambda commit: parse_istanbul("jest", commit),
    "vitest": lambda commit: parse_istanbul("vitest", commit),
    "java-maven": parse_java_maven,
    "go": parse_go,
}


def main():
    parser = argparse.ArgumentParser(description="Parse coverage output to unified JSON")
    parser.add_argument("--stack", required=True, choices=list(PARSERS.keys()))
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--commit", default="", help="Current git commit SHA")
    args = parser.parse_args()

    result = PARSERS[args.stack](args.commit)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    if result.get("warning") == "empty_coverage":
        print("WARNING: 0 lines tracked — coverage data is empty.")
        for hint in result.get("warning_hints", []):
            print(f"  • {hint}")
    else:
        print(f"Parsed {len(result['files'])} files → {args.output}")
        print(f"Overall: {result['overall']['percent']}% "
              f"({result['overall']['lines_hit']}/{result['overall']['lines_total']} lines)")


if __name__ == "__main__":
    main()
