#!/usr/bin/env python3
"""super-fork: Claude Code session fork manager with hierarchical pruning.

Core: byte-level JSONL copy with optional label, cwd relocation, desktop sidebar integration.
Management: delete, info, rename, tree, list — all registry-aware with trunk/branch/leaf roles.
Pruning: selective depth-based cleanup with trash + restore for safe recovery.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import sys
import time
import tempfile
import uuid as uuid_module
from datetime import datetime
from pathlib import Path


# ================================ paths & helpers ================================ #


def cwd_to_project_dir_name(cwd: str) -> str:
    return cwd.replace("/", "-")


def get_project_dir(cwd: str) -> Path:
    return Path.home() / ".claude" / "projects" / cwd_to_project_dir_name(cwd)


def desktop_sessions_root() -> Path:
    return Path.home() / "Library" / "Application Support" / "Claude" / "claude-code-sessions"


def labels_file_path() -> Path:
    return Path.home() / ".claude" / "super-fork-labels.json"


def registry_file_path() -> Path:
    return Path.home() / ".claude" / "super-fork-registry.json"


def trash_root() -> Path:
    return Path.home() / ".claude" / "super-fork-trash"


def now_ms() -> int:
    return int(time.time() * 1000)


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def depth_to_role(depth: int) -> str:
    return {0: "trunk", 1: "branch"}.get(depth, "leaf")


ROLE_ICON = {"trunk": "⬛", "branch": "🟦", "leaf": "🟩", "unknown": "⬜"}


def print_error(cause: str, **fields) -> None:
    lines = ["```", "❌ super-fork failed", f"   cause:       {cause}"]
    for key, value in fields.items():
        lines.append(f"   {key:12} {value}")
    lines.append("```")
    print("\n".join(lines), file=sys.stderr)


# ================================ fork core ================================ #


def find_current_session(project_dir: Path) -> Path:
    if not project_dir.is_dir():
        raise FileNotFoundError(f"project directory not found: {project_dir}")
    candidates = list(project_dir.glob("*.jsonl"))
    if not candidates:
        raise FileNotFoundError(f"no .jsonl sessions found in {project_dir}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def fork_jsonl(source: Path, project_dir: Path) -> str:
    new_uuid = str(uuid_module.uuid4())
    dest = project_dir / f"{new_uuid}.jsonl"
    while dest.exists():
        new_uuid = str(uuid_module.uuid4())
        dest = project_dir / f"{new_uuid}.jsonl"
    shutil.copy2(source, dest)
    return new_uuid


def rewrite_cwd_in_jsonl(jsonl_path: Path, source_cwd: str, target_cwd: str) -> int:
    source_cwd = source_cwd.rstrip("/")
    target_cwd = target_cwd.rstrip("/")
    if source_cwd == target_cwd:
        return 0
    old_pattern = '"cwd":"' + source_cwd + '"'
    new_pattern = '"cwd":"' + target_cwd + '"'
    count = 0
    fd, tmp_path = tempfile.mkstemp(dir=str(jsonl_path.parent), suffix=".tmp")
    try:
        with open(jsonl_path, "r") as src, os.fdopen(fd, "w") as dst:
            for line in src:
                if old_pattern in line:
                    line = line.replace(old_pattern, new_pattern, 1)
                    count += 1
                dst.write(line)
        shutil.copystat(str(jsonl_path), tmp_path)
        os.replace(tmp_path, jsonl_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return count


def inject_agent_name(jsonl_path: Path, agent_name: str, session_id: str) -> None:
    entry = {"type": "agent-name", "agentName": agent_name, "sessionId": session_id}
    with jsonl_path.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def root_hash(jsonl_path: Path) -> str:
    import hashlib
    with jsonl_path.open("rb") as f:
        return hashlib.md5(f.read(200)).hexdigest()


# ================================ desktop metadata ================================ #


def find_desktop_metadata(cli_session_id: str) -> Path | None:
    root = desktop_sessions_root()
    if not root.is_dir():
        return None
    for meta in root.rglob("local_*.json"):
        try:
            with meta.open() as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("cliSessionId") == cli_session_id:
            return meta
    return None


def create_desktop_metadata(
    source_meta_path: Path, fork_cli_uuid: str, label: str,
    target_cwd: str | None = None, title_override: str | None = None,
) -> Path | None:
    try:
        with source_meta_path.open() as f:
            source = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    new_local_id = f"local_{uuid_module.uuid4()}"
    new_meta = dict(source)
    new_meta["sessionId"] = new_local_id
    new_meta["cliSessionId"] = fork_cli_uuid
    now = now_ms()
    new_meta["createdAt"] = now
    new_meta["lastActivityAt"] = now
    new_meta["title"] = title_override if title_override else f"[s-fork] {label}"
    new_meta["isArchived"] = False
    new_meta["completedTurns"] = 0
    if target_cwd:
        new_meta["cwd"] = target_cwd
        new_meta["originCwd"] = target_cwd
    new_path = source_meta_path.parent / f"{new_local_id}.json"
    try:
        with new_path.open("w") as f:
            json.dump(new_meta, f, ensure_ascii=False, indent=2)
    except OSError:
        return None
    return new_path


# ================================ label backup store ================================ #


def _load_labels() -> dict:
    path = labels_file_path()
    if path.exists():
        try:
            with path.open() as f:
                d = json.load(f)
            if isinstance(d, dict) and isinstance(d.get("labels"), list):
                return d
        except (json.JSONDecodeError, OSError):
            pass
    return {"labels": []}


def _save_labels(data: dict) -> None:
    path = labels_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_label_backup(label: str, fork_uuid: str, source_uuid: str, cwd: str) -> None:
    data = _load_labels()
    data.setdefault("labels", []).append({
        "label": label, "fork_uuid": fork_uuid, "source_uuid": source_uuid,
        "cwd": cwd, "created_at": now_ms(),
    })
    try:
        _save_labels(data)
    except OSError:
        pass


# ================================ registry ================================ #


def _load_registry() -> dict:
    path = registry_file_path()
    if path.exists():
        try:
            with path.open() as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_registry(data: dict) -> None:
    path = registry_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def count_forks_from_source(source_uuid: str) -> int:
    reg = _load_registry()
    count = 0
    for proj in reg.values():
        for entry in proj.values():
            if isinstance(entry, dict) and entry.get("parent") == source_uuid:
                count += 1
    return count


def get_source_title(source_uuid: str) -> str | None:
    meta = find_desktop_metadata(source_uuid)
    if meta is not None:
        try:
            with meta.open() as f:
                data = json.load(f)
            title = data.get("title")
            if isinstance(title, str) and title.strip():
                t = title.strip()
                if t.startswith("[s-fork]"):
                    t = t[len("[s-fork]"):].strip()
                elif t.startswith("[s-fork:"):
                    idx = t.find("]")
                    if idx != -1:
                        t = t[idx + 1:].strip()
                return t if t else None
        except (json.JSONDecodeError, OSError):
            pass
    return None


def make_fork_prefix(fork_number: int) -> str:
    if fork_number <= 1:
        return "[s-fork]"
    return f"[s-fork: {fork_number}]"


def register_fork(project_key: str, source_uuid: str, fork_uuid: str) -> None:
    reg = _load_registry()
    proj = reg.setdefault(project_key, {})
    # Register source as trunk if not yet registered
    if source_uuid not in proj:
        proj[source_uuid] = {"depth": 0, "role": "trunk", "parent": None, "registered_at": now_ms()}
    source_depth = proj[source_uuid]["depth"]
    fork_depth = min(source_depth + 1, 2)
    proj[fork_uuid] = {
        "depth": fork_depth, "role": depth_to_role(fork_depth),
        "parent": source_uuid, "registered_at": now_ms(),
    }
    try:
        _save_registry(reg)
    except OSError:
        pass


def get_role(project_key: str, uuid: str) -> str:
    reg = _load_registry()
    entry = reg.get(project_key, {}).get(uuid)
    return entry["role"] if entry else "unknown"


def get_depth(project_key: str, uuid: str) -> int:
    reg = _load_registry()
    entry = reg.get(project_key, {}).get(uuid)
    return entry["depth"] if entry else -1


# ================================ trash system ================================ #


def move_to_trash(uuid: str, project_dir: Path, batch_dir: Path) -> dict:
    """Move a session's JSONL + metadata to trash. Returns manifest item."""
    item = {"uuid": uuid, "source_project_dir": str(project_dir)}
    jsonl = project_dir / f"{uuid}.jsonl"
    if jsonl.exists():
        shutil.move(str(jsonl), str(batch_dir / jsonl.name))
        item["jsonl"] = jsonl.name

    meta = find_desktop_metadata(uuid)
    if meta is not None:
        try:
            item["desktop_metadata_file"] = meta.name
            item["desktop_metadata_dir"] = str(meta.parent)
            shutil.move(str(meta), str(batch_dir / meta.name))
        except OSError:
            pass

    # Remove from labels
    data = _load_labels()
    for e in data.get("labels", []):
        if e.get("fork_uuid") == uuid:
            item["label"] = e.get("label")
            break
    data["labels"] = [e for e in data.get("labels", []) if e.get("fork_uuid") != uuid]
    try:
        _save_labels(data)
    except OSError:
        pass

    return item


def list_trash() -> int:
    root = trash_root()
    if not root.is_dir():
        print("🗑️  Trash is empty.")
        return 0
    batches = sorted(root.iterdir(), reverse=True)
    batches = [b for b in batches if b.is_dir() and (b / "manifest.json").exists()]
    if not batches:
        print("🗑️  Trash is empty.")
        return 0
    total_size = 0
    print(f"🗑️  Trash ({len(batches)} batch(es)):")
    for batch in batches:
        try:
            with (batch / "manifest.json").open() as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        items = manifest.get("items", [])
        batch_size = sum((batch / it.get("jsonl", "")).stat().st_size
                         for it in items if (batch / it.get("jsonl", "")).exists()) / 1024
        total_size += batch_size
        level = manifest.get("level", "?")
        ts = manifest.get("pruned_at", batch.name)
        print(f"\n  {ts}  pruned {level}  ({len(items)} session(s), {batch_size:.0f} KB)")
        for it in items:
            role = it.get("role", "?")
            label = it.get("label", "")
            icon = ROLE_ICON.get(role, "⬜")
            label_str = f"  [s-fork] {label}" if label else ""
            print(f"    {icon} {it['uuid'][:8]}...  [{role}]{label_str}")
    print(f"\n  total: {total_size:.0f} KB in trash")
    return 0


def restore_from_trash(target_uuid: str) -> int:
    root = trash_root()
    if not root.is_dir():
        print_error("trash is empty")
        return 1
    for batch in root.iterdir():
        manifest_path = batch / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            with manifest_path.open() as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        for item in manifest.get("items", []):
            if item.get("uuid") != target_uuid:
                continue
            # Found it — restore
            restored = []
            project_dir = Path(item.get("source_project_dir", ""))
            project_dir.mkdir(parents=True, exist_ok=True)
            jsonl_name = item.get("jsonl")
            if jsonl_name and (batch / jsonl_name).exists():
                shutil.move(str(batch / jsonl_name), str(project_dir / jsonl_name))
                restored.append("JSONL")
            meta_name = item.get("desktop_metadata_file")
            meta_dir = item.get("desktop_metadata_dir")
            if meta_name and (batch / meta_name).exists() and meta_dir:
                Path(meta_dir).mkdir(parents=True, exist_ok=True)
                shutil.move(str(batch / meta_name), str(Path(meta_dir) / meta_name))
                restored.append("desktop metadata")
            label = item.get("label")
            if label:
                data = _load_labels()
                data.setdefault("labels", []).append({
                    "label": label, "fork_uuid": target_uuid,
                    "source_uuid": item.get("parent", "?"),
                    "cwd": item.get("cwd", ""), "created_at": now_ms(),
                })
                try:
                    _save_labels(data)
                    restored.append("label")
                except OSError:
                    pass
            # Re-register in registry
            reg_entry = item.get("registry_entry")
            if reg_entry:
                reg = _load_registry()
                project_key = manifest.get("project_dir", "")
                reg.setdefault(project_key, {})[target_uuid] = reg_entry
                try:
                    _save_registry(reg)
                    restored.append("registry")
                except OSError:
                    pass
            # Clean up batch if empty
            manifest["items"] = [i for i in manifest["items"] if i["uuid"] != target_uuid]
            with manifest_path.open("w") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            if not manifest["items"]:
                shutil.rmtree(batch, ignore_errors=True)

            print(f"♻️  Restored {target_uuid}")
            print(f"   restored: {', '.join(restored)}")
            return 0

    print_error("uuid not found in trash", uuid=target_uuid)
    return 1


# ================================ prune ================================ #


def prune_forks(project_key: str, project_dir: Path, level: str, dry_run: bool) -> int:
    threshold = {"leaf": 2, "branch": 1}.get(level)
    if threshold is None:
        print_error(f"invalid prune level: {level}. Use 'leaf' or 'branch'.")
        return 1

    reg = _load_registry()
    proj = reg.get(project_key, {})
    if not proj:
        print("No registry entries for this project. Nothing to prune.")
        return 0

    # Find current session to protect
    try:
        current = find_current_session(project_dir)
        current_uuid = current.stem
    except FileNotFoundError:
        current_uuid = None

    targets = []
    for uuid, entry in proj.items():
        if entry["depth"] >= threshold and uuid != current_uuid:
            if (project_dir / f"{uuid}.jsonl").exists():
                targets.append((uuid, entry))

    if not targets:
        print(f"No {level} forks to prune.")
        return 0

    if dry_run:
        total_kb = sum((project_dir / f"{u}.jsonl").stat().st_size for u, _ in targets) / 1024
        print(f"🔍 Dry run — would prune {len(targets)} {level} fork(s) ({total_kb:.0f} KB):")
        for uuid, entry in targets:
            role = entry["role"]
            icon = ROLE_ICON.get(role, "⬜")
            size = (project_dir / f"{uuid}.jsonl").stat().st_size / 1024
            print(f"  {icon} {uuid[:8]}...  [{role}]  {size:.0f} KB")
        print(f"\n  Run without --dry-run to execute.")
        return 0

    # Execute prune → trash
    batch_name = now_iso()
    batch_dir = trash_root() / batch_name
    batch_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "pruned_at": batch_name, "project_dir": project_key,
        "level": level, "items": [],
    }

    for uuid, entry in targets:
        item = move_to_trash(uuid, project_dir, batch_dir)
        item["role"] = entry["role"]
        item["registry_entry"] = entry
        item["parent"] = entry.get("parent")
        manifest["items"].append(item)
        del proj[uuid]

    with (batch_dir / "manifest.json").open("w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    try:
        _save_registry(reg)
    except OSError:
        pass

    total_kb = sum((batch_dir / it.get("jsonl", "")).stat().st_size
                   for it in manifest["items"] if (batch_dir / it.get("jsonl", "")).exists()) / 1024

    print(f"🧹 Pruned {len(targets)} {level} fork(s) → trash")
    for it in manifest["items"]:
        icon = ROLE_ICON.get(it.get("role", ""), "⬜")
        label = f"  [s-fork] {it['label']}" if it.get("label") else ""
        print(f"  {icon} {it['uuid'][:8]}...  [{it.get('role', '?')}]{label}")
    print(f"   freed: {total_kb:.0f} KB  (recoverable via --restore)")
    return 0


# ================================ mark-trunk ================================ #


def _resolve_session_location(uuid: str, project_dir: Path, project_key: str):
    """Find a session JSONL across all project dirs. Returns (jsonl, project_key, project_dir) or None."""
    jsonl = project_dir / f"{uuid}.jsonl"
    if jsonl.exists():
        return jsonl, project_key, project_dir
    projects_root = Path.home() / ".claude" / "projects"
    if projects_root.is_dir():
        for d in projects_root.iterdir():
            if not d.is_dir() or d.name == project_dir.name:
                continue
            candidate = d / f"{uuid}.jsonl"
            if candidate.exists():
                return candidate, d.name, d
    return None


def mark_trunk(uuid: str, project_key: str, project_dir: Path) -> int:
    resolved = _resolve_session_location(uuid, project_dir, project_key)
    if resolved is None:
        print_error("session file not found", uuid=uuid)
        return 1
    _, resolved_key, resolved_dir = resolved
    reg = _load_registry()
    proj = reg.setdefault(resolved_key, {})
    proj[uuid] = {"depth": 0, "role": "trunk", "parent": None, "registered_at": now_ms()}
    try:
        _save_registry(reg)
    except OSError:
        print_error("failed to save registry")
        return 1
    if resolved_key != project_key:
        print(f"⬛ Marked as trunk: {uuid}  (found in {resolved_dir.name})")
    else:
        print(f"⬛ Marked as trunk: {uuid}")
    return 0


# ================================ adopt ================================ #


def _extract_embedded_session_id(jsonl_path: Path) -> str | None:
    """Read the first 100 lines of a JSONL to find the embedded sessionId."""
    try:
        with jsonl_path.open() as f:
            for i, line in enumerate(f):
                if i > 100:
                    break
                try:
                    obj = json.loads(line)
                    sid = obj.get("sessionId")
                    if isinstance(sid, str) and sid:
                        return sid
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return None


def adopt_sessions(project_key: str, project_dir: Path, confirm: bool) -> int:
    """Detect unregistered fork relationships and register them."""
    if not project_dir.is_dir():
        print("No project directory found.")
        return 0

    sessions = list(project_dir.glob("*.jsonl"))
    if not sessions:
        print("No sessions found.")
        return 0

    reg = _load_registry()
    proj = reg.get(project_key, {})
    already_registered = set(proj.keys())

    # Extract embedded sessionId for each unregistered session
    unregistered: dict[str, str | None] = {}
    for s in sessions:
        if s.stem not in already_registered:
            unregistered[s.stem] = _extract_embedded_session_id(s)

    if not unregistered:
        print("All sessions are already registered.")
        return 0

    # Find fork relationships:
    # A session is a fork if its embedded sessionId != its filename UUID
    # AND the embedded sessionId corresponds to another session's filename
    all_filenames = {s.stem for s in sessions}
    candidates: dict[str, list[str]] = {}  # trunk_uuid -> [fork_uuids]

    for uuid, embedded in unregistered.items():
        if embedded and embedded != uuid and embedded in all_filenames:
            candidates.setdefault(embedded, []).append(uuid)

    if not candidates:
        print(f"🔍 No fork relationships detected among {len(unregistered)} unregistered session(s).")
        return 0

    # Display candidates
    total_forks = sum(len(forks) for forks in candidates.values())
    print(f"🔍 Adopt candidates ({len(candidates)} trunk(s), {total_forks} fork(s)):\n")

    for trunk_uuid, fork_uuids in sorted(candidates.items()):
        trunk_in_reg = trunk_uuid in already_registered
        trunk_status = "already registered" if trunk_in_reg else "→ trunk"
        trunk_jsonl = project_dir / f"{trunk_uuid}.jsonl"
        trunk_size = trunk_jsonl.stat().st_size / 1024 if trunk_jsonl.exists() else 0
        print(f"  ⬛ {trunk_uuid[:8]}...  {trunk_size:>7.0f}KB  ({trunk_status})")
        for fork_uuid in fork_uuids:
            fork_jsonl = project_dir / f"{fork_uuid}.jsonl"
            fork_size = fork_jsonl.stat().st_size / 1024 if fork_jsonl.exists() else 0
            print(f"    🟦 {fork_uuid[:8]}...  {fork_size:>7.0f}KB  → branch (embedded={trunk_uuid[:8]}...)")

    skipped = len(unregistered) - total_forks - len([t for t in candidates if t not in already_registered])
    if skipped > 0:
        print(f"\n  Skipped: {skipped} independent session(s) (no fork relationships)")

    if not confirm:
        print(f"\n  Run with --confirm to register these.")
        return 0

    # Execute registration
    registered_count = 0
    for trunk_uuid, fork_uuids in candidates.items():
        if trunk_uuid not in proj:
            proj[trunk_uuid] = {
                "depth": 0, "role": "trunk", "parent": None, "registered_at": now_ms(),
            }
            registered_count += 1
        for fork_uuid in fork_uuids:
            if fork_uuid not in proj:
                proj[fork_uuid] = {
                    "depth": 1, "role": "branch", "parent": trunk_uuid, "registered_at": now_ms(),
                }
                registered_count += 1

    reg[project_key] = proj
    try:
        _save_registry(reg)
    except OSError:
        print_error("failed to save registry")
        return 1

    print(f"\n✅ Adopted {registered_count} session(s) into registry.")
    return 0


# ================================ enhanced list ================================ #


def list_labels_enhanced(project_key: str) -> int:
    data = _load_labels()
    entries = data.get("labels", [])
    if not entries:
        print("No labeled forks yet. Use `/super-fork --name <label>` to create one.")
        return 0
    print(f"Labeled forks ({len(entries)}):")
    for e in sorted(entries, key=lambda x: x.get("created_at", 0), reverse=True):
        ts_ms = e.get("created_at", 0)
        dt = datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M") if ts_ms else "unknown"
        label = e.get("label", "(no label)")
        fork_uuid = e.get("fork_uuid", "?")
        source_uuid = e.get("source_uuid", "?")
        role = get_role(project_key, fork_uuid)
        icon = ROLE_ICON.get(role, "⬜")
        print(f"  {dt}   {icon} [{role:7}]  [{label}]")
        print(f"    fork:   claude --resume {fork_uuid}")
        print(f"    source: {source_uuid}")
    return 0


# ================================ enhanced tree ================================ #


def show_tree_enhanced(project_dir: Path, project_key: str) -> int:
    if not project_dir.is_dir():
        print("No project directory found.")
        return 0
    sessions = list(project_dir.glob("*.jsonl"))
    if not sessions:
        print("No sessions found.")
        return 0

    reg = _load_registry()
    proj = reg.get(project_key, {})

    def get_title(uuid: str) -> str:
        meta = find_desktop_metadata(uuid)
        if meta:
            try:
                with meta.open() as f:
                    return json.load(f).get("title", "")
            except (json.JSONDecodeError, OSError):
                pass
        return ""

    # Build parent→children map from registry
    children_map: dict[str | None, list[str]] = {}
    registered_uuids = set()
    for uuid, entry in proj.items():
        parent = entry.get("parent")
        children_map.setdefault(parent, []).append(uuid)
        registered_uuids.add(uuid)

    # Identify sessions on disk
    on_disk = {s.stem for s in sessions}

    # Print registered trees first
    printed = set()

    def print_subtree(uuid: str, prefix: str, is_last: bool):
        if uuid in printed or uuid not in on_disk:
            return
        printed.add(uuid)
        entry = proj.get(uuid, {})
        role = entry.get("role", "unknown")
        icon = ROLE_ICON.get(role, "⬜")
        jsonl = project_dir / f"{uuid}.jsonl"
        size = jsonl.stat().st_size / 1024 if jsonl.exists() else 0
        mtime = datetime.fromtimestamp(jsonl.stat().st_mtime).strftime("%m/%d %H:%M") if jsonl.exists() else ""
        title = get_title(uuid)
        title_str = f"  {title}" if title else ""
        connector = "└─" if is_last else "├─"
        if prefix == "":
            print(f"\n  {icon} {uuid[:8]}...  [{role:7}]  {size:>7.0f}KB  {mtime}{title_str}")
        else:
            print(f"  {prefix}{connector} {icon} {uuid[:8]}...  [{role:7}]  {size:>7.0f}KB  {mtime}{title_str}")
        kids = children_map.get(uuid, [])
        kids = [k for k in kids if k in on_disk]
        for i, kid in enumerate(kids):
            child_prefix = prefix + ("   " if is_last else "│  ")
            print_subtree(kid, child_prefix, i == len(kids) - 1)

    # Find roots (trunks / entries with no parent in registry)
    roots = [u for u, e in proj.items() if e.get("parent") is None and u in on_disk]

    print(f"🌳 Session tree ({len(sessions)} sessions):")

    for root_uuid in sorted(roots, key=lambda u: -(project_dir / f"{u}.jsonl").stat().st_mtime if (project_dir / f"{u}.jsonl").exists() else 0):
        print_subtree(root_uuid, "", True)

    # Print unregistered sessions
    unregistered = on_disk - printed
    if unregistered:
        for uuid in sorted(unregistered, key=lambda u: -(project_dir / f"{u}.jsonl").stat().st_mtime):
            jsonl = project_dir / f"{uuid}.jsonl"
            size = jsonl.stat().st_size / 1024
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime).strftime("%m/%d %H:%M")
            title = get_title(uuid)
            title_str = f"  {title}" if title else ""
            print(f"\n  ⬜ {uuid[:8]}...  [unknown]  {size:>7.0f}KB  {mtime}{title_str}")

    return 0


# ================================ delete / info / rename ================================ #


def delete_fork(target_uuid: str, project_dir: Path, project_key: str) -> int:
    resolved = _resolve_session_location(target_uuid, project_dir, project_key)
    if resolved is None:
        print_error("session file not found", uuid=target_uuid)
        return 1
    jsonl, resolved_key, resolved_dir = resolved
    try:
        current = find_current_session(resolved_dir)
        if current.stem == target_uuid:
            print_error("refusing to delete the most recently active session", uuid=target_uuid)
            return 1
    except FileNotFoundError:
        pass

    removed = []
    jsonl.unlink()
    removed.append("JSONL")

    meta = find_desktop_metadata(target_uuid)
    if meta is not None:
        try:
            meta.unlink()
            removed.append("desktop metadata")
        except OSError:
            pass

    data = _load_labels()
    before = len(data.get("labels", []))
    data["labels"] = [e for e in data.get("labels", []) if e.get("fork_uuid") != target_uuid]
    if len(data["labels"]) < before:
        try:
            _save_labels(data)
            removed.append("label")
        except OSError:
            pass

    reg = _load_registry()
    proj = reg.get(resolved_key, {})
    if target_uuid in proj:
        del proj[target_uuid]
        try:
            _save_registry(reg)
            removed.append("registry")
        except OSError:
            pass

    if resolved_key != project_key:
        print(f"🗑️  Deleted fork {target_uuid}  (found in {resolved_dir.name})")
    else:
        print(f"🗑️  Deleted fork {target_uuid}")
    print(f"   removed: {', '.join(removed)}")
    return 0


def show_info(target_uuid: str, project_dir: Path, project_key: str) -> int:
    resolved = _resolve_session_location(target_uuid, project_dir, project_key)
    if resolved is None:
        print_error("session file not found", uuid=target_uuid)
        return 1
    jsonl, resolved_key, resolved_dir = resolved

    stat = jsonl.stat()
    size_kb = stat.st_size / 1024
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    lines = sum(1 for _ in jsonl.open())

    role = get_role(resolved_key, target_uuid)
    depth = get_depth(resolved_key, target_uuid)
    icon = ROLE_ICON.get(role, "⬜")

    my_hash = root_hash(jsonl)
    siblings = [o.stem for o in resolved_dir.glob("*.jsonl")
                if o.stem != target_uuid and root_hash(o) == my_hash]

    embedded_id = None
    with jsonl.open() as f:
        for i, line in enumerate(f):
            if i > 50:
                break
            try:
                obj = json.loads(line)
                if isinstance(obj.get("sessionId"), str):
                    embedded_id = obj["sessionId"]
                    break
            except json.JSONDecodeError:
                continue
    is_fork = embedded_id and embedded_id != target_uuid

    meta = find_desktop_metadata(target_uuid)
    title = meta_cwd = model = turns = None
    if meta is not None:
        try:
            md = json.load(meta.open())
            title, meta_cwd, model, turns = md.get("title"), md.get("cwd"), md.get("model"), md.get("completedTurns")
        except (json.JSONDecodeError, OSError):
            pass

    label = None
    for e in _load_labels().get("labels", []):
        if e.get("fork_uuid") == target_uuid:
            label = e.get("label")
            break

    print(f"📋 Session info: {target_uuid}")
    if resolved_key != project_key:
        print(f"   found in: {resolved_dir.name}")
    print(f"   role:     {icon} {role}" + (f" (depth {depth})" if depth >= 0 else ""))
    print(f"   size:     {size_kb:.0f} KB ({lines} lines)")
    print(f"   modified: {mtime}")
    if title:
        print(f"   title:    {title}")
    if label:
        print(f"   label:    {label}")
    if model:
        print(f"   model:    {model}")
    if turns is not None:
        print(f"   turns:    {turns}")
    if meta_cwd:
        print(f"   cwd:      {meta_cwd}")
    if is_fork:
        print(f"   fork of:  {embedded_id}")
    if siblings:
        print(f"   siblings: {len(siblings)} other session(s) in same lineage")
    return 0


def _extract_fork_prefix(title: str) -> str:
    if title.startswith("[s-fork:"):
        idx = title.find("]")
        if idx != -1:
            return title[:idx + 1]
    if title.startswith("[s-fork]"):
        return "[s-fork]"
    return "[s-fork]"


def rename_fork(target_uuid: str, new_name: str, project_dir: Path, project_key: str = "") -> int:
    resolved = _resolve_session_location(target_uuid, project_dir, project_key)
    if resolved is None:
        print_error("session file not found", uuid=target_uuid)
        return 1
    jsonl, _, _ = resolved
    existing_prefix = "[s-fork]"
    updated = []
    meta = find_desktop_metadata(target_uuid)
    if meta is not None:
        try:
            md = json.load(meta.open())
            existing_title = md.get("title", "")
            if isinstance(existing_title, str):
                existing_prefix = _extract_fork_prefix(existing_title)
            new_title = f"{existing_prefix} {new_name}"
            md["title"] = new_title
            with meta.open("w") as f:
                json.dump(md, f, ensure_ascii=False, indent=2)
            updated.append("desktop sidebar")
        except (json.JSONDecodeError, OSError):
            pass
    else:
        new_title = f"{existing_prefix} {new_name}"
    data = _load_labels()
    for e in data.get("labels", []):
        if e.get("fork_uuid") == target_uuid:
            e["label"] = new_name
            updated.append("backup label")
            break
    try:
        _save_labels(data)
    except OSError:
        pass
    if updated:
        print(f"✏️  Renamed → {new_title}")
        print(f"   updated: {', '.join(updated)}")
    else:
        print(f"✏️  Renamed → {new_title}")
        print(f"   note: no desktop metadata or label found to update")
    return 0


# ================================ argument parsing ================================ #


def parse_args(argv: list[str]) -> argparse.Namespace:
    if len(argv) == 1 and argv[0].strip() and (" " in argv[0] or '"' in argv[0]):
        argv = shlex.split(argv[0])
    argv = [a for a in argv if a.strip()]
    parser = argparse.ArgumentParser(prog="super-fork", add_help=False)
    parser.add_argument("source", nargs="?", default=None)
    parser.add_argument("-n", "--name", default=None)
    parser.add_argument("--cwd", default=None)
    parser.add_argument("-l", "--list", action="store_true")
    parser.add_argument("--delete", default=None, metavar="UUID")
    parser.add_argument("--info", default=None, metavar="UUID")
    parser.add_argument("--rename", nargs=2, metavar=("UUID", "NAME"))
    parser.add_argument("--tree", action="store_true")
    parser.add_argument("--prune", default=None, choices=["leaf", "branch"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--trash", action="store_true")
    parser.add_argument("--restore", default=None, metavar="UUID")
    parser.add_argument("--mark-trunk", default=None, metavar="UUID")
    parser.add_argument("--adopt", action="store_true",
                        help="detect and register unregistered fork relationships")
    parser.add_argument("--confirm", action="store_true",
                        help="execute adoption (use with --adopt)")
    parser.add_argument("-h", "--help", action="store_true")
    args, unknown = parser.parse_known_args(argv)
    extra_name_parts = list(unknown)
    if args.name and args.source:
        try:
            uuid_module.UUID(args.source.strip())
        except ValueError:
            extra_name_parts.insert(0, args.source)
            args.source = None
    if args.name and extra_name_parts:
        args.name = args.name + " " + " ".join(extra_name_parts)
    elif not args.name and unknown:
        parser.parse_args(argv)
    return args


def print_usage() -> None:
    print(
        "super-fork usage:\n"
        "  /super-fork                               fork the current session\n"
        '  /super-fork --name "label"                fork current with a label\n'
        "  /super-fork --cwd ~/path                  fork into a different project dir\n"
        "  /super-fork --list                        list labeled forks (with roles)\n"
        "  /super-fork --tree                        show fork lineage tree\n"
        "  /super-fork --info <uuid>                 show session details + role\n"
        "  /super-fork --delete <uuid>               delete a fork\n"
        '  /super-fork --rename <uuid> "name"        rename a fork label\n'
        "  /super-fork --prune leaf                  prune leaf forks → trash\n"
        "  /super-fork --prune branch                prune branch+leaf forks → trash\n"
        "  /super-fork --prune leaf --dry-run        preview what would be pruned\n"
        "  /super-fork --trash                       show trash contents\n"
        "  /super-fork --restore <uuid>              restore from trash\n"
        "  /super-fork --mark-trunk <uuid>           designate a session as trunk\n"
        "  /super-fork --adopt                       detect unregistered fork relationships\n"
        "  /super-fork --adopt --confirm             register detected forks"
    )


# ================================ main ================================ #


def main() -> int:
    args = parse_args(sys.argv[1:])

    if args.help:
        print_usage()
        return 0

    source_cwd = os.getcwd()
    project_key = cwd_to_project_dir_name(source_cwd)
    project_dir = get_project_dir(source_cwd)

    # Dispatch management commands
    if args.list:
        return list_labels_enhanced(project_key)
    if args.tree:
        return show_tree_enhanced(project_dir, project_key)
    if args.delete:
        return delete_fork(args.delete.strip(), project_dir, project_key)
    if args.info:
        return show_info(args.info.strip(), project_dir, project_key)
    if args.rename:
        return rename_fork(args.rename[0].strip(), args.rename[1].strip(), project_dir, project_key)
    if args.prune:
        return prune_forks(project_key, project_dir, args.prune, args.dry_run)
    if args.trash:
        return list_trash()
    if args.restore:
        return restore_from_trash(args.restore.strip())
    if args.mark_trunk:
        return mark_trunk(args.mark_trunk.strip(), project_key, project_dir)
    if args.adopt:
        return adopt_sessions(project_key, project_dir, args.confirm)

    # --- Fork flow ---
    source_project_dir = project_dir
    if args.cwd:
        target_cwd = os.path.realpath(os.path.expanduser(args.cwd))
        Path(target_cwd).mkdir(parents=True, exist_ok=True)
        target_project_dir = get_project_dir(target_cwd)
        target_project_dir.mkdir(parents=True, exist_ok=True)
    else:
        target_cwd = source_cwd
        target_project_dir = source_project_dir

    try:
        if args.source:
            source_uuid = args.source.strip()
            if source_uuid.endswith(".jsonl"):
                source_uuid = source_uuid[: -len(".jsonl")]
            source = source_project_dir / f"{source_uuid}.jsonl"
            if not source.exists():
                print_error("source session file not found", uuid=source_uuid)
                return 1
        else:
            source = find_current_session(source_project_dir)
            source_uuid = source.stem
    except FileNotFoundError as e:
        print_error(str(e))
        return 1

    try:
        new_uuid = fork_jsonl(source, target_project_dir)
    except OSError as e:
        print_error(f"failed to copy: {e}")
        return 1

    cwd_rewrite_count = 0
    if target_cwd != source_cwd:
        try:
            cwd_rewrite_count = rewrite_cwd_in_jsonl(
                target_project_dir / f"{new_uuid}.jsonl", source_cwd, target_cwd)
        except Exception as e:
            print(f"   ⚠️  cwd rewrite failed ({e}); fork copied without rewrite",
                  file=sys.stderr)

    # Register in hierarchy
    target_project_key = cwd_to_project_dir_name(target_cwd)
    register_fork(project_key, source_uuid, new_uuid)
    if target_project_key != project_key:
        register_fork(target_project_key, source_uuid, new_uuid)

    # Session naming: always apply [s-fork] prefix with auto-numbering
    fork_number = count_forks_from_source(source_uuid)
    prefix = make_fork_prefix(fork_number)

    if args.name:
        display_name = args.name.strip()
    else:
        display_name = get_source_title(source_uuid) or source_uuid[:8]

    session_name = f"{prefix} {display_name}"
    fork_jsonl_path = target_project_dir / f"{new_uuid}.jsonl"

    inject_agent_name(fork_jsonl_path, session_name, new_uuid)
    try:
        with open(fork_jsonl_path, "a") as f:
            f.write(json.dumps({"type": "custom-title", "customTitle": session_name,
                                "sessionId": new_uuid}) + "\n")
    except OSError:
        pass

    label_status = ""
    source_meta = find_desktop_metadata(source_uuid)
    metadata_path = None
    if source_meta is not None:
        metadata_path = create_desktop_metadata(
            source_meta, new_uuid, display_name,
            target_cwd=target_cwd, title_override=session_name)

    if args.name:
        append_label_backup(args.name.strip(), new_uuid, source_uuid, target_cwd)

    if metadata_path is not None:
        label_status = f"   name:    {session_name}  (desktop sidebar + backup)"
    else:
        label_status = f"   name:    {session_name}  (backup only)"

    role = get_role(project_key, new_uuid)
    icon = ROLE_ICON.get(role, "⬜")
    print(f"✅ Forked → {new_uuid}  {icon} [{role}]")
    print(f"   source:  {source_uuid}")
    if target_cwd != source_cwd:
        print(f"   cwd:     {source_cwd} → {target_cwd}")
        if cwd_rewrite_count > 0:
            print(f"   rewrite: {cwd_rewrite_count} cwd field(s) updated")
        print(f"   resume:  cd {target_cwd} && claude --resume {new_uuid}")
    else:
        print(f"   resume:  claude --resume {new_uuid}")
    if label_status:
        print(label_status)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print_error(f"unexpected error: {e}")
        sys.exit(1)
