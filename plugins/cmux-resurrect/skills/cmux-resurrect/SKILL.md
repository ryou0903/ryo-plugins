---
description: "This skill should be used when the user asks to save cmux workspace state, restore workspaces after reboot, check snapshot status, or mentions 'c-save', 'c-restore', 'cmux-resurrect', 'workspace save', 'workspace restore'."
---

# cmux-resurrect

Save and restore cmux workspaces and CLI agent sessions after Mac reboot.

## Commands

Run these via the Bash tool:

| Command | Description |
|---------|-------------|
| `c-save` | Manually save current workspace state (manual snapshot line) |
| `c-restore` | Restore workspaces from the best available snapshot |
| `c-restore-dry` | Preview what would be restored without executing |
| `c-restore-list` | List available snapshots (manual + auto) |

## How It Works

- **Auto-save**: launchd runs every 5 minutes, writing to auto snapshot line
- **Manual save**: `c-save` writes to manual snapshot line (separate file, never overwritten by auto)
- **Restore**: picks the newer of manual/auto snapshots, creates cmux workspaces, and resumes Claude Code sessions with `--resume`
- **Two-line save**: auto save never overwrites manual save. Empty snapshots (0 sessions) are never written.

## Snapshot Location

`~/.local/state/cmux-resurrect/`:
- `workspace-snapshot-auto.json` — auto-save (launchd timer)
- `workspace-snapshot-manual.json` — manual save only
