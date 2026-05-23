# env-registry Guideline

Rules for writing and maintaining entries in `~/.claude/env-registry/`.

## File placement

| Category | Path | What goes here |
|---|---|---|
| platforms | `platforms/<name>.md` | OS/device-level info (mac, windows, galaxy) |
| mcp-servers | `mcp-servers/<name>.md` | MCP server configurations |
| plugins | `plugins/<name>.md` | Claude Code plugins, IDE plugins |
| skills | `skills/<name>.md` | Claude Code skills (slash-command invocable) |
| services | `services/<name>.md` | Background services, daemons, localhost endpoints |
| clis | `clis/<name>.md` | CLI tools, shell helpers, shell functions |

## Category decision hints

When a tool spans multiple categories, use these rules:
- **Primary function wins**: `gws` is a CLI even though it talks to a service. Category = `clis`.
- **If it runs in background without user invocation**: `services`
- **If the primary interface is a slash command in Claude Code**: `skills`
- **If it's an MCP server config**: `mcp-servers` (even if it wraps a CLI)
- **If unsure**: prefer `clis` for anything invoked from terminal, `services` for anything with a port/daemon.
- **Never duplicate**: one entry, one category. Use `related` section to cross-reference.

## File naming

- Lowercase, kebab-case: `google-workspace-cli.md`, `claude-mem.md`
- One entry per file. Never merge unrelated tools into one file.

## Entry format

Every entry is a single markdown file with YAML frontmatter + structured body.

```yaml
---
name: <display name>
category: <platforms|mcp-servers|plugins|skills|services|clis>
platform: [mac]              # which devices this applies to; omit if universal
status: installed             # installed | available | deprecated | broken | outdated | inactive
version: <version or null>
updated: <YYYY-MM-DD>
tags: [<free-form tags>]
source_url: <repo or homepage, optional>
install_method: <brew|npm|pip|cargo|manual|appstore|apt|bundled|other, optional>
---
```

## Body sections

Include only sections that have content. Order:

1. **purpose** (1 line) — what this thing does
2. **commands** — table of commands/subcommands
3. **examples** — common usage patterns (under 10 rows)
4. **endpoints** — URLs with port, description, prerequisites
5. **paths** — important file/directory paths on disk
6. **auth** — authentication details if any
7. **shell_helpers** — zsh/bash functions related to this entry
8. **notes** — gotchas, known issues, workarounds
9. **related** — links to other env-registry entries

## Section formatting

### commands

```markdown
| Command | Description |
|---|---|
| `npx claude-mem start` | Start worker process |
| `npx claude-mem uninstall` | Full uninstall |
```

### examples

```markdown
| Scenario | Command |
|---|---|
| デバイスにAPKインストール | `adb install app.apk` |
| ログをフィルタして監視 | `adb logcat -s "MyApp"` |
```

### endpoints

```markdown
| URL | Description | Requires |
|---|---|---|
| `http://localhost:37777` | Memory browser UI | Worker running |
```

### paths

```markdown
| Path | Description |
|---|---|
| `~/.claude-mem/settings.json` | Config file |
```

### shell_helpers

```markdown
| Function | Description |
|---|---|
| `nclaw-reset <group>` | Full reset of a NanoClaw group |
```

## INDEX.md

`~/.claude/env-registry/INDEX.md` is a lightweight pointer file. One line per entry, grouped by category. Format:

```
## <Category>
- [<name>](<category>/<filename>.md) — <one-line summary, under 80 chars>
```

Keep INDEX.md sorted alphabetically within each category. Update it every time an entry is added, removed, or renamed.

## Update policy

- When an entry's version, URL, command, or status changes, update the entry AND bump `updated:` in frontmatter.
- When a tool is uninstalled, set `status: deprecated` and add a note. Do not delete the file (history is useful).
- When migrating from QMD or other sources, rewrite content to match this format. Do not copy prose verbatim.

## Writing style

- Written for AI consumption, not humans.
- Terse. No prose paragraphs. Tables and key-value pairs preferred.
- Japanese descriptions (matching Ryo's language).
- Technical identifiers (commands, paths, URLs) stay in English.
