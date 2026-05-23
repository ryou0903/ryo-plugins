---
name: super-fork
description: Fork the current Claude Code session (copy its JSONL to a new UUID, optionally with a human-readable label or relocated to a different working directory) ONLY when the user explicitly runs /super-fork. This skill must not trigger autonomously — it runs solely on explicit user invocation via the slash command.
argument-hint: '[--name "label"] [--cwd path] [uuid] | --list | --tree | --delete <uuid> | --info <uuid> | --rename <uuid> "name" | --mark-trunk <uuid> | --prune leaf|branch [--dry-run] | --trash | --restore <uuid> | --adopt [--confirm]'
allowed-tools: Bash(python3:*)
---

# super-fork

Claude Code session fork manager with hierarchical pruning. Byte-level JSONL copy with optional label, cwd relocation, desktop sidebar integration, lineage tree, and trash-based safe cleanup.

## All commands

### Fork (core)

| Command | Action |
|---------|--------|
| `/super-fork` | Fork the current (most recently modified) session |
| `/super-fork <uuid>` | Fork a specific session by UUID |
| `/super-fork --name "label"` | Fork current session with a label |
| `/super-fork --name "label" <uuid>` | Fork a specific session with a label |
| `/super-fork --cwd ~/new/path` | Fork into a different project directory |
| `/super-fork --cwd ~/path --name "label"` | Relocate + label |

### Inspect

| Command | Action |
|---------|--------|
| `/super-fork --list` | List all labeled forks with roles |
| `/super-fork --tree` | Show fork lineage tree (trunk → branch → leaf) |
| `/super-fork --info <uuid>` | Show session details: role, size, lines, title, model, turns, siblings |

### Manage

| Command | Action |
|---------|--------|
| `/super-fork --rename <uuid> "name"` | Rename a fork label (desktop sidebar + backup) |
| `/super-fork --delete <uuid>` | Permanently delete a fork (JSONL + metadata + label + registry) |
| `/super-fork --mark-trunk <uuid>` | Designate a session as trunk (depth 0) in the hierarchy |

### Prune and trash

| Command | Action |
|---------|--------|
| `/super-fork --prune leaf` | Move all leaf forks to trash |
| `/super-fork --prune branch` | Move all branch + leaf forks to trash |
| `/super-fork --prune leaf --dry-run` | Preview what would be pruned |
| `/super-fork --trash` | Show trash contents |
| `/super-fork --restore <uuid>` | Restore a session from trash |

### Adopt

| Command | Action |
|---------|--------|
| `/super-fork --adopt` | Detect unregistered fork relationships (dry-run) |
| `/super-fork --adopt --confirm` | Register detected fork relationships |

## Hierarchy model

Sessions have three roles based on depth:

| Role | Depth | Icon | Meaning |
|------|-------|------|---------|
| trunk | 0 | ⬛ | Main line (original or promoted via `--mark-trunk`) |
| branch | 1 | 🟦 | Direct fork of trunk |
| leaf | 2 | 🟩 | Fork of a branch (max depth) |
| unknown | - | ⬜ | Not yet registered |

`--mark-trunk` promotes any session to depth 0. Use after forking when the fork becomes the main line of work.

## Execution

Run the fork script with the user's arguments passed through **quoted** so special characters (brackets, spaces) are preserved:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/super-fork/scripts/fork.py" "$ARGUMENTS"
```

**Always quote `"$ARGUMENTS"`** in this invocation. The script detects a single-string argument and uses `shlex.split` internally for correct parsing.

## Critical: bare positional arguments are UUIDs

A bare string without flags is treated as a **session UUID**, not a label name:

```
/super-fork my-label           ← WRONG: "my-label" parsed as UUID → not found
/super-fork --name "my-label"  ← CORRECT: labeled fork
```

## Output handling

On success, the script prints 3-5 lines to stdout depending on options used. Relay the output to the user as-is — do not reformat, do not add commentary, do not rewrite the resume command.

Example output:

```
✅ Forked → 73a18acb-164f-4538-9724-31a90db556b1  🟦 [branch]
   source:  36495033-7039-4b47-a482-7518a09da7a1
   cwd:     /Users/ryo/.../cn-nanoclaw → /Users/ryo/.../cn-claw
   resume:  cd /Users/ryo/.../cn-claw && claude --resume 73a18acb-...
   label:   [s-fork] テスト  (desktop sidebar + backup)
```

If the desktop metadata store is unavailable, the label line will say `(backup only)`. That is expected, not an error.

On failure, the script prints a diagnostic block (already wrapped in triple backticks) to stderr. Relay it verbatim.

## Common patterns

### Fork + resume with new MCP

When a new MCP server was added mid-session and needs to be loaded:

```
/super-fork --name "with-new-mcp"
→ resume the fork in a new tab → MCP loads fresh
→ /super-fork --mark-trunk <new-uuid>  (if the fork becomes main)
```

### Prune old forks

```
/super-fork --tree              ← review the hierarchy
/super-fork --prune leaf --dry-run  ← preview
/super-fork --prune leaf        ← move leaves to trash
/super-fork --trash             ← verify
```

## Strict behavior rules

- **Explicit-invocation only.** Do not invoke this skill based on conversation context, "helpful" assumptions, or perceived user intent. It runs solely when the user types `/super-fork`.
- **Source file is never modified.** The fork is a byte-level copy.
- **Do not auto-resume.** The resume command is printed so the user can decide when and where to open the new session.
- **The `[s-fork]` prefix is added automatically.** Do not instruct the user to include it, and do not strip it.
- **`--cwd` auto-creates the target directory.** If the specified path doesn't exist on disk, the script creates it. Do not warn the user about missing directories.
