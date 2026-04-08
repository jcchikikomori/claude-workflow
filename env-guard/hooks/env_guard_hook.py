#!/usr/bin/env python3
"""
env-guard PreToolUse hook for Claude Code.

Blocks Claude from reading, writing, editing, or shell-leaking sensitive
credential files such as .env files, SSH keys, cloud credentials, and tokens.

Exit codes (PreToolUse contract):
  0 - Allow the tool call to proceed
  2 - Block the tool call; stderr message is fed back to Claude as context
"""

import json
import re
import sys

# ---------------------------------------------------------------------------
# Sensitive FILE path patterns (regex applied to tool_input.file_path)
# ---------------------------------------------------------------------------
# Each pattern is tested against the full file path (forward-slash normalized).
# Explicit allow-list exceptions (.env.example, .env.sample) are checked first.

ALLOWED_FILE_PATTERNS = [
    # Template / example dotenv files are safe — they contain no real secrets
    r"(^|/)\.env\.(example|sample|template)$",
    r"(^|/)\.env\.example\.",
]

SENSITIVE_FILE_PATTERNS = [
    # dotenv files: .env, .env.local, .env.production, app.env, etc.
    r"(^|/)\.env($|\.(?!example|sample|template))",
    r"(^|/)[^/]+\.env$",
    # Cloud credentials
    r"(^|/)credentials(\.json)?$",
    r"\.aws/credentials$",
    r"\.azure/credentials$",
    r"(^|/)service[_-]account.*\.json$",
    r"gcloud/.*credentials",
    # SSH private keys
    r"\.ssh/(id_rsa|id_dsa|id_ecdsa|id_ed25519|id_ed25519_sk|id_ecdsa_sk)$",
    r"(^|/)id_rsa$",
    r"\.(pem|key)$",
    # TLS / PKI
    r"\.(pfx|p12)$",
    r"(^|/)(server|private)\.key$",
    # Token / auth files
    r"(^|/)\.netrc$",
    r"(^|/)\.pypirc$",
    r"(^|/)\.htpasswd$",
    r"(^|/)(auth|token)\.json$",
    r"(^|/)[^/]+\.token$",
    # Secret config files
    r"(^|/)secrets?\.(json|ya?ml|txt)$",
    r"(^|/)\.secrets?$",
    # Database credential files
    r"(^|/)\.pgpass$",
    r"(^|/)pgpass$",
    # Terraform variable files (may contain secrets)
    r"(^|/)terraform\.tfvars$",
    r"(^|/)[^/]+\.tfvars$",
    r"(^|/)override\.tf$",
    # Key stores
    r"\.(jks|keystore)$",
    # Shell history (can contain secrets from past commands)
    r"(^|/)\.(bash|zsh|fish|python|node_repl)_history$",
    # Docker / k8s secret overlays
    r"(^|/)docker-compose\.override\.ya?ml$",
    r"[_-]secrets?\.ya?ml$",
]

# ---------------------------------------------------------------------------
# Sensitive BASH command patterns (regex applied to tool_input.command)
# ---------------------------------------------------------------------------
# These commands print environment variables or read credential files directly.

SENSITIVE_BASH_PATTERNS = [
    (r"^\s*env\s*$", "Running bare `env` prints all environment variables"),
    (r"^\s*printenv\b", "`printenv` prints environment variables"),
    (r"^\s*set\s*$", "Running bare `set` dumps shell variables including secrets"),
    (r"\bexport\s+-p\b", "`export -p` dumps all exported variables"),
    (r"\becho\s+['\"]?\$[A-Z_]{4,}", "`echo $UPPERCASE_VAR` may expose secret values"),
    (r"\bcat\s+['\"]?[^\s;|&]*\.env\b", "`cat` on a .env file exposes secrets"),
    (r"\bcat\s+['\"]?~/\.ssh/", "`cat` on SSH keys exposes private key material"),
    (r"\bcat\s+['\"]?~/\.aws/credentials", "`cat` on AWS credentials exposes keys"),
    (r"\bcat\s+['\"]?~/\.netrc\b", "`cat` on .netrc exposes stored passwords"),
    (r"\bcat\s+['\"]?[^\s;|&]*credentials\b", "`cat` on credentials file exposes secrets"),
    (r"\bcat\s+['\"]?[^\s;|&]*\.pem\b", "`cat` on a .pem file exposes private key material"),
    (r"\bcat\s+['\"]?[^\s;|&]*\.key\b", "`cat` on a .key file exposes private key material"),
]

BLOCK_FILE_MESSAGE = """\
[env-guard] BLOCKED: Access to '{path}' is not permitted.

This file matches a sensitive credential pattern. To protect secrets from
accidental exposure, env-guard prevents Claude from reading, writing, or
editing this file type.

If this is a false positive, the user can grant access by adding a
permissions.allow rule in .claude/settings.json:

  {{ "permissions": {{ "allow": ["Read({path})"] }} }}
"""

BLOCK_BASH_MESSAGE = """\
[env-guard] BLOCKED: The command may expose secrets or credentials.

Reason: {reason}

Commands that print environment variables or read credential files are blocked.
If this operation is genuinely needed, the user should run it directly in a
terminal — outside of Claude Code.
"""


def is_allowed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(re.search(p, normalized) for p in ALLOWED_FILE_PATTERNS)


def is_sensitive_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(re.search(p, normalized) for p in SENSITIVE_FILE_PATTERNS)


def is_sensitive_bash(command: str) -> tuple[bool, str]:
    for pattern, reason in SENSITIVE_BASH_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
            return True, reason
    return False, ""


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # Parse failure: allow rather than block

    tool_name: str = data.get("tool_name", "")
    tool_input: dict = data.get("tool_input", {})

    if tool_name in ("Read", "Write", "Edit", "MultiEdit"):
        path: str = tool_input.get("file_path", "")
        if not path:
            sys.exit(0)

        # Explicit allow-list takes precedence (e.g. .env.example)
        if is_allowed_path(path):
            sys.exit(0)

        if is_sensitive_path(path):
            print(BLOCK_FILE_MESSAGE.format(path=path), file=sys.stderr)
            sys.exit(2)

    elif tool_name == "Bash":
        command: str = tool_input.get("command", "")
        if not command:
            sys.exit(0)

        blocked, reason = is_sensitive_bash(command)
        if blocked:
            print(BLOCK_BASH_MESSAGE.format(reason=reason), file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
