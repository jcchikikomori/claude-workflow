# claude-attribution

Ensures every external post made through any MCP-connected platform carries a visible AI-authorship attribution line:

> 🤖 Written by Claude, reviewed by \<name\>

## How It Works

- A **PreToolUse hook** matches all MCP tools (`mcp__.*`) and Bash commands dynamically — no hardcoded platform names.
- The hook scans `tool_input` for body-like fields (`body`, `content`, `message`, `comment`, `commentBody`, `description`, `text`).
- Posts missing the attribution line are **blocked before they are sent**.
- A companion **skill** instructs Claude to include the attribution proactively and to **show the post to the user for review before sending**.

## Supported Platforms

Works with **any** MCP-connected platform, including:

- GitHub (PRs, issues, review comments)
- JIRA (issue comments, descriptions)
- Confluence (pages, comments)
- Slack (messages)
- Any future MCP server with body-like fields

Also covers CLI tools: `gh pr create`, `gh pr comment`, `gh issue comment`, `gh api`, `curl POST/PUT/PATCH`, etc.

## Setup

### 1. Install the plugin

```bash
/plugin install claude-attribution@claude-workflow
/reload-plugins
```

### 2. Set your name (first use)

The plugin will prompt for your name on first use. You can also set it manually:

```bash
echo "Your Name" > ~/.claude/claude-attribution-name.txt
```

## User Review Flow

Before posting to any external platform, Claude will:

1. Compose the post with the attribution line
2. Show the **complete post content** to the user
3. Ask for approval before sending
4. Only post after user confirms

## Version History

### 0.2.0

- Expanded Bash pattern coverage: `gh pr edit`, `gh issue edit`, `gh api ... -f body=`
- Fixed false positive on `gh pr merge` (no text body, should not block)
- Hook block messages now enforce user approval flow before retry
- Added user review requirement to skill and hook messages

### 0.1.0

- Initial release
- Dynamic MCP tool detection via body-field scanning
- PreToolUse hook + behavioral skill (dual-layer enforcement)
- User name config at `~/.claude/claude-attribution-name.txt`
- Covers GitHub, JIRA, Confluence, Slack, and any MCP server
