#!/usr/bin/env python3
"""cmux-resurrect CLI — save, restore, list workspace snapshots.

Usage:
  cli.py --save [--auto]     Save current workspaces (manual or auto line)
  cli.py --restore           Restore from best snapshot
  cli.py --dry-run           Preview restore without executing
  cli.py --list              List available snapshots
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import resurrect


def cmd_save(auto=False):
    source = "auto" if auto else "manual"
    snapshot = resurrect.save(source)
    if not snapshot:
        if not auto:
            print("No active sessions to save.")
        return 0

    session_count = sum(len(w["sessions"]) for w in snapshot["workspaces"])
    print("Saved [{}] {} workspace(s), {} session(s)".format(
        source, len(snapshot["workspaces"]), session_count))
    for ws in snapshot["workspaces"]:
        for s in ws["sessions"]:
            print("  [{}] {}... ({})".format(ws["title"], s["cli_session_id"][:12], s["tab_title"]))
    return 0


def cmd_restore(dry_run=False):
    snapshot = resurrect.load()
    if not snapshot:
        print("No workspace snapshot found.")
        return 0

    total = sum(len(w.get("sessions", [])) for w in snapshot["workspaces"])
    print("Snapshot [{}] from {}: {} workspace(s), {} session(s)".format(
        snapshot.get("source", "?"), snapshot["saved_at"],
        len(snapshot["workspaces"]), total))

    if total == 0:
        print("Nothing to restore.")
        return 0

    if dry_run:
        print("\nDRY RUN preview:\n")
        for ws in snapshot["workspaces"]:
            print("  workspace: \"{}\"".format(ws["title"]))
            for s in ws.get("sessions", []):
                print("    {} {}... -> {} ({})".format(
                    s.get("cli", "?"), s.get("cli_session_id", "?")[:8],
                    s.get("cwd", "?"), s.get("tab_title", "")))
        return 0

    result = resurrect.restore(snapshot)
    if "error" in result:
        print("Error: {}".format(result["error"]))
        return 1

    print("\nRestored {} workspace(s), {} session(s)".format(
        result["restored_workspaces"], result["restored_sessions"]))
    if result.get("errors"):
        print("Errors ({}):".format(len(result["errors"])))
        for e in result["errors"]:
            print("  - {}".format(e))
    return 0


def cmd_list():
    snapshots = resurrect.list_snapshots()
    if not snapshots:
        print("No snapshots found.")
        return 0
    for s in snapshots:
        print("[{}] {} — {} workspace(s), {} session(s)".format(
            s["type"], s["saved_at"], s["workspaces"], s["sessions"]))
    return 0


def main():
    args = sys.argv[1:]

    if "--save" in args:
        return cmd_save(auto="--auto" in args)
    elif "--dry-run" in args:
        return cmd_restore(dry_run=True)
    elif "--restore" in args:
        return cmd_restore()
    elif "--list" in args:
        return cmd_list()
    else:
        print(__doc__.strip())
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("Fatal: {}".format(e), file=sys.stderr)
        sys.exit(1)
