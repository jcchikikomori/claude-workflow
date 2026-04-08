---
name: env-guard
description: Behavioral guardrail for secret and credential protection. Use when working with environment variables, configuration files, deployment settings, or any operation that may touch .env files, API keys, tokens, SSH keys, or cloud credentials. Reinforces that Claude must never read or expose sensitive credentials.
---

# env-guard: Credential and Secret Protection

## Core Rule

**Never read, print, or expose the contents of sensitive credential files.**

The `env-guard` PreToolUse hook enforces this at the tool level. This skill
reinforces the behavioral intent so Claude avoids attempting blocked actions
in the first place.

## Off-Limits File Categories

The following files are always protected unless the user explicitly grants access:

| Category | Examples |
|---|---|
| dotenv files | `.env`, `.env.local`, `.env.production`, `.env.staging`, `app.env` |
| Cloud credentials | `~/.aws/credentials`, `service-account.json`, gcloud auth files |
| SSH private keys | `~/.ssh/id_rsa`, `~/.ssh/id_ed25519`, any `*.pem`, `*.key` |
| TLS / PKI | `*.pfx`, `*.p12`, `server.key`, `private.key` |
| Token / auth files | `.netrc`, `.pypirc`, `.htpasswd`, `token.json`, `auth.json`, `*.token` |
| Secret configs | `secrets.json`, `secrets.yml`, `terraform.tfvars`, `*.tfvars` |
| Shell history | `.bash_history`, `.zsh_history`, `.python_history` |

**Exception:** `.env.example`, `.env.sample`, and `.env.template` files are
safe — they contain placeholder values, not real secrets. Read these freely.

## Bash Commands to Avoid

Do not run commands that dump or print credentials:

- `env` — prints all environment variables
- `printenv` — prints environment variables
- `set` — dumps shell variables including any exported secrets
- `export -p` — dumps all exported variables
- `echo $SECRET_VAR` or `echo $UPPERCASE_VAR` — may expose secret values
- `cat .env*`, `cat credentials`, `cat ~/.ssh/*`, `cat ~/.aws/credentials`
- `cat *.pem`, `cat *.key` — exposes private key material

## Permitted Alternatives

When a task requires knowing which environment variables exist (not their values):

- Read `.env.example` or `.env.sample` to understand the expected variable names
- Ask the user: "What is the name of the variable that holds the database URL?"
- Suggest the user verify the value themselves in their terminal
- Use `env | grep -i PATTERN` **only to confirm existence**, never to print values

When helping a user configure secrets:

- Reference variable names only (e.g., `DATABASE_URL`, `API_KEY`)
- Generate `.env.example` content with placeholder values
- Never reconstruct a secret from context clues or partial information

## When the Hook Blocks a Tool Call

1. Do **not** retry the same blocked operation
2. Explain to the user that `env-guard` prevented the access and why
3. Suggest what they can do instead (e.g., read `.env.example`, check docs)
4. If the user believes it is a false positive, direct them to add an allow rule:
   ```json
   { "permissions": { "allow": ["Read(./path/to/file)"] } }
   ```
