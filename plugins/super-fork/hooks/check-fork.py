#!/usr/bin/env python3
"""super-fork SessionStart hook: detect forked sessions and tell Claude.

A session is considered forked when the embedded `sessionId` field in the JSONL
messages does not match the filename's UUID. Emits a short one-line notice on
the FIRST resume only — subsequent resumes are silent.

Non-fatal by design: any error results in silent exit 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MARKER = '"subtype":"fork_awareness_delivered"'


def cwd_to_project_dir_name(cwd: str) -> str:
    return cwd.replace("/", "-")


def find_embedded_session_id(jsonl_path: Path) -> tuple[str | None, str | None]:
    session_id = None
    original_cwd = None
    try:
        with jsonl_path.open() as f:
            for i, line in enumerate(f):
                if i > 50:
                    break
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if session_id is None and isinstance(obj.get("sessionId"), str):
                    session_id = obj["sessionId"]
                if original_cwd is None and isinstance(obj.get("cwd"), str) and obj["cwd"]:
                    original_cwd = obj["cwd"]
                if session_id and original_cwd:
                    break
    except OSError:
        pass
    return session_id, original_cwd


def already_notified(jsonl_path: Path) -> bool:
    try:
        with jsonl_path.open() as f:
            for line in f:
                if MARKER in line:
                    return True
    except OSError:
        pass
    return False


def write_marker(jsonl_path: Path, current_session_id: str) -> None:
    marker_entry = {
        "type": "system",
        "subtype": "fork_awareness_delivered",
        "sessionId": current_session_id,
        "isMeta": True,
    }
    try:
        with jsonl_path.open("a") as f:
            f.write(json.dumps(marker_entry) + "\n")
    except OSError:
        pass


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    current_session_id = hook_input.get("session_id")
    current_cwd = hook_input.get("cwd")
    if not current_session_id or not current_cwd:
        return 0

    project_dir = Path.home() / ".claude" / "projects" / cwd_to_project_dir_name(current_cwd)
    jsonl_path = project_dir / f"{current_session_id}.jsonl"
    if not jsonl_path.exists():
        return 0

    embedded_id, embedded_cwd = find_embedded_session_id(jsonl_path)
    if not embedded_id:
        return 0

    if embedded_id == current_session_id:
        return 0

    if already_notified(jsonl_path):
        return 0

    cwd_changed = embedded_cwd and embedded_cwd != current_cwd
    if cwd_changed:
        context = (
            f"⚠️ Forked session (original: {embedded_id[:12]}…, cwd: {embedded_cwd} → {current_cwd}). "
            f"Conversation history is from the original. You are an independent session.\n"
            f"**IMPORTANT**: Working directory changed. You MUST re-activate Serena for the new project "
            f"directory ({current_cwd}) before using any Serena tools. The previous project context is stale."
        )
    else:
        context = f"⚠️ Forked session (original: {embedded_id[:12]}…). Conversation history is from the original. You are an independent session."

    write_marker(jsonl_path, current_session_id)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
