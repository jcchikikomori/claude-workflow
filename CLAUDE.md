# CLAUDE.md — claude-workflow

This is a personal fork of [@shinpr](https://github.com/shinpr)'s [claude-code-workflows](https://github.com/shinpr/claude-code-workflows), maintained as a custom Claude Code marketplace at `jcchikikomori/claude-workflow`.

## Fork Relationship

- **Upstream:** `https://github.com/shinpr/claude-code-workflows`
- **This fork:** `https://github.com/jcchikikomori/claude-workflow`
- **License:** MIT — original copyright by Shinsuke Kagawa is preserved in `LICENSE`

Upstream changes should be periodically merged in. When rebasing onto a new upstream release, update the plugin versions accordingly (see versioning below).

## Versioning Convention

This fork uses a **fork qualifier suffix** on top of upstream's SemVer: `<upstream-version>-jcc.<fork-patch>`.

Examples:

| plugin.json `version` | git tag | Meaning |
| --------------------- | ------- | ------- |
| `0.16.11-jcc.1` | `v0.16.11-jcc.1` | First fork change on upstream `0.16.11` |
| `0.16.11-jcc.2` | `v0.16.11-jcc.2` | Second fork change, same upstream base |
| `0.17.0-jcc.1` | `v0.17.0-jcc.1` | Reset fork patch after merging upstream `0.17.0` |

### `v` prefix convention

Git tags use a `v` prefix (`v0.16.11-jcc.1`) — this is the git-flow convention configured for this repository. The `version` field in plugin.json files does **not** use the `v` prefix, as JSON metadata parsers treat it as a bare SemVer string.

### Why this approach

SemVer pre-release identifiers (the `-` suffix) sort *below* the base version in strict SemVer precedence. This correctly signals that `0.16.11-jcc.1` is a derivative of `0.16.11`, not a newer release. It also lets consumers and tooling distinguish fork builds from upstream builds.

Alternatives considered:

- **Build metadata** (`0.16.11+jcc.1`) — no precedence effect, purely informational, less visible
- **Independent versioning** (reset to `1.0.0`) — loses traceability to upstream base

### Files that carry version numbers (fork-qualified)

- `plugin-dev/.claude-plugin/plugin.json`
- `plugin-qa/.claude-plugin/plugin.json`
- `plugin-env-guard/.claude-plugin/plugin.json`

All three must be kept in sync. Update them together whenever the version changes.

### Independently versioned plugins

- `plugin-attribution/.claude-plugin/plugin.json` — uses plain SemVer (`0.1.0`, `0.2.0`, ...), **not** the fork-qualified `jcc.N` scheme, because it is an original plugin with no upstream counterpart.

### When to bump versions

**Fork-qualified plugins** (`dev`, `qa`, `env-guard`): Increment `jcc.N` when you make changes to plugin logic, skills, or agents — not for branding-only edits. The fork patch resets to `jcc.1` whenever upstream base version changes.

**Independently versioned plugins** (`claude-attribution`): Bump the SemVer version in `plugin.json` after every change to plugin logic, hooks, or skills. Use minor version for new features/behavior changes, patch for bug fixes.

**After every plugin change**, also update the plugin's `README.md` with a changelog entry describing what changed.

## Using This as a Custom Marketplace

### Install the marketplace in Claude Code

```bash
# Inside a Claude Code session
/plugin marketplace add jcchikikomori/claude-workflow
```

This registers the marketplace from the GitHub repo. Claude Code reads `.claude-plugin/marketplace.json` to discover available plugins.

### Install a plugin from this marketplace

```bash
/plugin install dev@claude-workflow
/plugin install qa@claude-workflow
/plugin install env-guard@claude-workflow
/plugin install claude-attribution@claude-workflow

# External add-ons (pulled from their own repos)
/plugin install metronome@claude-workflow
/plugin install discover@claude-workflow
```

### Apply changes after install or update

```bash
/reload-plugins
```

Always reload after installing, updating, or switching plugins within the same session.

### Plugin categories

| Plugin | Type | What it provides |
| ------ | ---- | --------------- |
| `dev` | workflow-orchestration | Agent-driven recipes for web, mobile, and integration development |
| `qa` | product-quality | Agent-driven recipes for acceptance tests, E2E, and browser-layer QA |
| `env-guard` | behavior-control | Hook enforcement to prevent leaking .env and secrets |
| `claude-attribution` | governance | Hook + skill ensuring all MCP-posted content carries a "Written by Claude, reviewed by \<user\>" attribution line |
| `skills` ([skills-md](https://github.com/jcchikikomori/skills-md)) | language/framework rules | Technology-specific coding standards — Ruby, Python, React, Node.js, Docker, etc. |

The `dev` and `qa` plugins cover **workflow orchestration** — how to plan, build, and verify software using AI agents. The `skills` plugin (from the separate `skills-md` repo) covers **language and framework rules** — what good code looks like in a given technology. They complement each other and can be installed together.

### claude-attribution plugin

**Purpose:** Ensures every external post made through any MCP-connected platform (GitHub, JIRA, Confluence, Slack, etc.) carries a visible AI-authorship attribution line.

**How it works:**

- A `PreToolUse` hook matches the pattern `mcp__.*|Bash` — this catches all MCP tools dynamically without hardcoding platform names.
- The hook scans `tool_input` for body-like fields (`body`, `content`, `message`, `comment`, `commentBody`, `description`, `text`).
- Posts missing the attribution line are blocked before they are sent.
- A companion skill instructs Claude to include the attribution proactively and to show the post to the user for review before sending.

**User configuration:** The user's name is stored in `~/.claude/claude-attribution-name.txt`. On first use the plugin prompts for the name so the attribution reads correctly (e.g., "Written by Claude, reviewed by Jane").

---

## Adding a Custom Plugin

### Step 1 — Create the plugin directory

```text
my-plugin/
├── .claude-plugin/
│   └── plugin.json       # Plugin metadata and asset references
├── skills/               # Optional: skill definitions
│   └── my-skill/
│       └── SKILL.md
└── agents/               # Optional: agent definitions
    └── my-agent.md
```

### Step 2 — Write `plugin.json`

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "One-line description of what this plugin does",
  "author": {
    "name": "John Cyrill Corsanes",
    "url": "https://github.com/jcchikikomori"
  },
  "homepage": "https://github.com/jcchikikomori/claude-workflow",
  "repository": "https://github.com/jcchikikomori/claude-workflow.git",
  "license": "MIT",
  "keywords": ["your", "tags", "here"]
}
```

To register skills and agents, add them as arrays:

```json
{
  "skills": [
    "./skills/my-skill"
  ],
  "agents": [
    "./agents/my-agent.md"
  ]
}
```

### Step 3 — Write a skill (`SKILL.md`)

Skills are knowledge guides injected into the Claude context when invoked.

```markdown
---
name: my-skill
description: Brief description — used by Claude to decide when to load this skill.
---

# My Skill Title

Your skill content here. Write it as guidance Claude should follow.
```

The `description` field is critical — Claude uses it for relevance matching when deciding whether to apply the skill.

### Step 4 — Write an agent (`.md`)

Agents are subagents launched via the `Agent` tool with specialized roles.

```markdown
---
name: my-agent
description: What this agent does and when to use it. Be specific — this text appears in the agent picker.
tools: Read, Grep, Glob, Bash, Edit, Write
skills: coding-principles, testing-principles
---

Your agent system prompt here. Define the agent's role, inputs, outputs, and behavior.
```

Common `tools` values: `Read`, `Grep`, `Glob`, `LS`, `Bash`, `Edit`, `Write`, `MultiEdit`, `TaskCreate`, `TaskUpdate`, `WebSearch`.

`skills` lists skill names (not paths) that the agent loads automatically.

### Step 5 — Register in `marketplace.json`

Open `.claude-plugin/marketplace.json` and add an entry to the `plugins` array:

```json
{
  "name": "my-plugin",
  "source": "./my-plugin",
  "description": "What this plugin does"
}
```

For plugins hosted in a separate repository:

```json
{
  "name": "my-plugin",
  "source": {
    "source": "url",
    "url": "https://github.com/jcchikikomori/my-plugin.git"
  },
  "description": "What this plugin does",
  "category": "workflow-orchestration",
  "homepage": "https://github.com/jcchikikomori/my-plugin"
}
```

Valid `category` values: `product-quality`, `behavior-control`, `quality-enforcement`, `workflow-orchestration`, `governance`, `safety-verification`.

---

## Marketplace Structure

```bash
.claude-plugin/marketplace.json   # Marketplace registry (owner: jcchikikomori)
plugin-dev/                       # dev plugin — web, mobile, integrations (DEV agents + skills)
plugin-qa/                        # qa plugin — web, mobile, integration testing (QA agents + skills)
plugin-env-guard/                 # env-guard plugin — secrets leak prevention
plugin-attribution/               # claude-attribution plugin — AI authorship attribution on MCP posts
```

Each plugin owns its agents and skills directly — no shared root directories, no symlinks. To update an agent or skill, edit it in the plugin directory where it belongs (`plugin-dev/agents/`, `plugin-qa/skills/`, etc.).

External plugins (`metronome`, `discover`) are referenced by URL and maintained by their original authors. Do not modify their source URLs.

## Platform Support

| Platform | Status |
| -------- | ------ |
| macOS | Supported |
| Linux | Supported |
| WSL (Windows) | Supported |
| Native Windows | Supported |

Plugin files are copied directly — no symlinks. Full compatibility across all platforms including native Windows.

`.gitattributes` is configured to normalize line endings to LF, which prevents CRLF issues in WSL and other environments.

## Merging Upstream Changes

1. `git fetch upstream`
2. `git merge upstream/main` (or rebase — resolve conflicts in plugin.json author/homepage fields)
3. Update all three `version` fields (`plugin-dev`, `plugin-qa`, `plugin-env-guard`) to `<new-upstream-version>-jcc.1`
4. Verify branding fields (author, homepage, repository) were not overwritten by the merge
