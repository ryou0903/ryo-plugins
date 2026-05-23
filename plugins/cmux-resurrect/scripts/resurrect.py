#!/usr/bin/env python3
"""cmux-resurrect core — save and restore cmux workspaces with CLI agent sessions.

Socket-first (0.2ms/op, no process spawn), CLI fallback (287ms/op).
Two-line save: auto (launchd timer) + manual (c-save).
"""

from __future__ import annotations
import json
import os
import re
import socket
import subprocess
import sys
import uuid as uuid_mod
from datetime import datetime
from pathlib import Path

SNAPSHOT_DIR = Path.home() / ".local" / "state" / "cmux-resurrect"
AUTO_FILE = SNAPSHOT_DIR / "workspace-snapshot-auto.json"
MANUAL_FILE = SNAPSHOT_DIR / "workspace-snapshot-manual.json"

SOCKET_PATHS = [
    os.environ.get("CMUX_SOCKET_PATH", ""),
    str(Path.home() / "Library" / "Application Support" / "cmux" / "cmux.sock"),
]

AGENT_ENV = "MCP_CONNECTION_NONBLOCKING=1 CLAUDE_CODE_NO_FLICKER=1"

RESUME_CMDS = {
    "claude": "claude --dangerously-skip-permissions --resume {sid}",
    "codex": "codex resume {sid}",
    "gemini": "gemini --resume {sid}",
    "kiro": "kiro-cli chat --resume-id {sid}",
    "cursor": "cursor agent --resume {sid}",
    "hermes": "hermes --resume {sid}",
}

STATUS_ICON_RE = re.compile(r'^[✳⠐⠒⠇⠋⠙⠸⠴⠦⠂]\s*')


# ── Socket client ──

class CmuxSocket:
    def __init__(self, path):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect(path)
        self.buf = b""

    def call(self, method, params=None):
        msg = {"id": str(uuid_mod.uuid4()), "method": method}
        if params:
            msg["params"] = params
        self.sock.sendall((json.dumps(msg) + "\n").encode())
        while True:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("socket closed")
            self.buf += chunk
            while b"\n" in self.buf:
                line, self.buf = self.buf.split(b"\n", 1)
                try:
                    resp = json.loads(line)
                    if resp.get("id") == msg["id"]:
                        if "error" in resp:
                            raise RuntimeError(resp["error"])
                        return resp.get("result", {})
                except json.JSONDecodeError:
                    continue

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def connect_socket():
    for p in SOCKET_PATHS:
        if p and Path(p).exists():
            try:
                return CmuxSocket(p)
            except (OSError, ConnectionError):
                continue
    return None


# ── CLI fallback ──

def cmux_cli(*args):
    result = subprocess.run(
        ["cmux"] + list(args),
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip()


def strip_icon(s):
    return STATUS_ICON_RE.sub('', s)


# ── Data gathering ──

def get_workspaces_socket(sock):
    result = sock.call("workspace.list")
    return result if isinstance(result, list) else result.get("workspaces", [])


def get_surfaces_socket(sock, ws_id):
    result = sock.call("surface.list", {"workspace_id": ws_id})
    return result if isinstance(result, list) else result.get("surfaces", [])


def parse_tree(text):
    workspaces = []
    current_ws = None
    current_surfaces = []
    tty_re = re.compile(r'tty=(ttys\d+)')

    for line in text.split("\n"):
        ws_m = re.search(r'workspace (\S+)\s+"([^"]*)"', line)
        surf_m = re.search(r'surface (\S+)\s+\[terminal\]\s+"([^"]*)"', line)

        if ws_m:
            if current_ws:
                workspaces.append({"ref": current_ws[0], "title": current_ws[1], "surfaces": current_surfaces})
            current_ws = (ws_m.group(1), strip_icon(ws_m.group(2).strip()))
            current_surfaces = []

        if surf_m:
            tty_m = tty_re.search(line)
            current_surfaces.append({
                "ref": surf_m.group(1),
                "title": strip_icon(surf_m.group(2).strip()),
                "tty": tty_m.group(1) if tty_m else "",
            })

    if current_ws:
        workspaces.append({"ref": current_ws[0], "title": current_ws[1], "surfaces": current_surfaces})
    return workspaces


def get_workspaces_cli():
    try:
        raw = subprocess.run(["cmux", "tree", "--all"], capture_output=True, text=True, timeout=5)
        return parse_tree(raw.stdout)
    except Exception:
        return []


def get_tty_cwd(tty):
    try:
        ps = subprocess.run(["ps", "-t", tty, "-o", "pid="], capture_output=True, text=True, timeout=3)
        pids = [p.strip() for p in ps.stdout.strip().split("\n") if p.strip()]
        if not pids:
            return ""
        lsof = subprocess.run(
            ["lsof", "-a", "-d", "cwd", "-p", pids[-1], "-Fn"],
            capture_output=True, text=True, timeout=3,
        )
        for line in lsof.stdout.split("\n"):
            if line.startswith("n/"):
                return line[1:]
    except Exception:
        pass
    return ""


def cwd_to_project_key(cwd):
    return cwd.replace("/", "-")


def find_latest_session(cwd):
    if not cwd:
        return ""
    proj_dir = Path.home() / ".claude" / "projects" / cwd_to_project_key(cwd)
    if not proj_dir.is_dir():
        return ""
    best = ""
    best_mtime = 0
    for jsonl in proj_dir.glob("*.jsonl"):
        mt = jsonl.stat().st_mtime
        if mt > best_mtime:
            best_mtime = mt
            best = jsonl.stem
    return best


# ── Multi-CLI detection ──

RESUME_ARG_RE = re.compile(r'--resume(?:\s+|=)(\S+)')
CODEX_RESUME_RE = re.compile(r'codex\s+resume\s+(\S+)')


def detect_cli(tty):
    try:
        ps = subprocess.run(
            ["ps", "-t", tty, "-o", "comm,args"],
            capture_output=True, text=True, timeout=3,
        )
        out = ps.stdout
        if "claude" in out:
            return "claude"
        if "codex" in out:
            return "codex"
        if "hermes" in out:
            return "hermes"
    except Exception:
        pass
    return "shell"


def extract_session_from_args(tty):
    try:
        ps = subprocess.run(
            ["ps", "-t", tty, "-o", "args="],
            capture_output=True, text=True, timeout=3,
        )
        m = RESUME_ARG_RE.search(ps.stdout)
        if m:
            return m.group(1)
        m = CODEX_RESUME_RE.search(ps.stdout)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""


def find_codex_session(cwd):
    index = Path.home() / ".codex" / "session_index.jsonl"
    if not index.exists():
        return ""
    best_id = ""
    best_ts = ""
    try:
        with open(index) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    ts = entry.get("updated_at", "")
                    if ts > best_ts:
                        best_ts = ts
                        best_id = entry.get("session_id", entry.get("id", ""))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return best_id


def find_hermes_session():
    profiles_dir = Path.home() / ".hermes" / "profiles"
    if not profiles_dir.is_dir():
        return ""
    best_id = ""
    best_ts = ""
    try:
        for profile in profiles_dir.iterdir():
            sfile = profile / "sessions" / "sessions.json"
            if not sfile.exists():
                continue
            with open(sfile) as f:
                data = json.load(f)
            for _key, entry in data.items():
                ts = entry.get("updated_at", "")
                if ts > best_ts:
                    best_ts = ts
                    best_id = entry.get("session_id", "")
    except Exception:
        pass
    return best_id


def resolve_session(tty, cwd):
    cli = detect_cli(tty)
    sid = extract_session_from_args(tty)
    if not sid:
        if cli == "claude":
            sid = find_latest_session(cwd)
        elif cli == "codex":
            sid = find_codex_session(cwd)
        elif cli == "hermes":
            sid = find_hermes_session()
    return cli, sid


# ── Save ──

def build_snapshot(source):
    sock = connect_socket()
    if sock:
        try:
            ws_list = get_workspaces_socket(sock)
            workspaces = []
            for ws in ws_list:
                ws_ref = ws.get("ref", ws.get("id", ""))
                ws_title = strip_icon(ws.get("title", "Workspace"))
                surfaces = get_surfaces_socket(sock, ws_ref)
                surf_list = []
                for s in surfaces:
                    if s.get("type") != "terminal":
                        continue
                    surf_list.append({
                        "ref": s.get("ref", ""),
                        "title": strip_icon(s.get("title", "")),
                        "tty": "",
                    })
                workspaces.append({"ref": ws_ref, "title": ws_title, "surfaces": surf_list})
            sock.close()
            sock = None
            tree_data = get_workspaces_cli()
            tty_map = {}
            for tw in tree_data:
                for ts in tw.get("surfaces", []):
                    tty_map[ts["ref"]] = ts.get("tty", "")
            for ws in workspaces:
                for s in ws["surfaces"]:
                    s["tty"] = tty_map.get(s["ref"], s["tty"])
        except Exception:
            if sock:
                sock.close()
            workspaces = get_workspaces_cli()
    else:
        workspaces = get_workspaces_cli()

    seen_sessions = set()
    ws_snapshots = []
    for ws in workspaces:
        sessions = []
        for surf in ws.get("surfaces", []):
            tty = surf.get("tty", "")
            if not tty:
                continue
            cwd = get_tty_cwd(tty)
            cli, session_id = resolve_session(tty, cwd)

            if cli == "shell":
                if cwd:
                    sessions.append({
                        "cli_session_id": "",
                        "cli": "shell",
                        "cwd": cwd,
                        "tab_title": surf.get("title", ""),
                    })
                continue

            if not session_id or session_id in seen_sessions:
                continue
            seen_sessions.add(session_id)
            sessions.append({
                "cli_session_id": session_id,
                "cli": cli,
                "cwd": cwd,
                "tab_title": surf.get("title", ""),
            })
        if sessions:
            ws_snapshots.append({
                "title": ws.get("title", "Workspace"),
                "cwd": sessions[0]["cwd"] if sessions else "",
                "sessions": sessions,
            })

    if not ws_snapshots:
        return None

    return {
        "version": 1,
        "saved_at": datetime.now().isoformat(),
        "source": source,
        "workspaces": ws_snapshots,
    }


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.rename(path)


def save(source="manual"):
    target = AUTO_FILE if source == "auto" else MANUAL_FILE
    snapshot = build_snapshot(source)
    if not snapshot:
        return None
    atomic_write(target, snapshot)
    return snapshot


# ── Load ──

def _load_file(path):
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        if data.get("version") != 1 or not isinstance(data.get("workspaces"), list):
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def load():
    manual = _load_file(MANUAL_FILE)
    auto = _load_file(AUTO_FILE)
    if manual and auto:
        mt = datetime.fromisoformat(manual["saved_at"])
        at = datetime.fromisoformat(auto["saved_at"])
        return manual if mt >= at else auto
    return manual or auto


def load_manual():
    return _load_file(MANUAL_FILE)


def load_auto():
    return _load_file(AUTO_FILE)


# ── Resume command ──

def build_resume_command(cli, cwd, session_id):
    if cli == "shell":
        return "cd {}".format(cwd) if cwd else ""
    cd = "cd {} && ".format(cwd) if cwd else ""
    tmpl = RESUME_CMDS.get(cli, "{env} {cli} --resume {sid}")
    if cli not in RESUME_CMDS:
        return "{}{} {} --resume {}".format(cd, AGENT_ENV, cli, session_id)
    return "{}{}".format(cd, AGENT_ENV + " " + tmpl.format(sid=session_id))


# ── Restore ──

import time as _time

def restore(snapshot=None, dry_run=False):
    if snapshot is None:
        snapshot = load()
    if not snapshot:
        return {"error": "No snapshot found"}

    total = sum(len(w.get("sessions", [])) for w in snapshot["workspaces"])
    if total == 0:
        return {"error": "Snapshot is empty"}

    if dry_run:
        return {"dry_run": True, "snapshot": snapshot}

    sock = connect_socket()
    if sock:
        try:
            return _restore_socket(sock, snapshot)
        finally:
            sock.close()
    else:
        return _restore_cli(snapshot)


def _restore_socket(sock, snapshot):
    restored_ws = 0
    restored_sessions = 0
    errors = []

    for ws in snapshot["workspaces"]:
        sessions = ws.get("sessions", [])
        if not sessions:
            continue
        try:
            result = sock.call("workspace.create", {"title": ws["title"]})
            ws_id = result.get("workspace_id", result.get("workspace_ref", result.get("id", "")))
        except Exception as e:
            errors.append("workspace \"{}\": {}".format(ws["title"], e))
            continue
        restored_ws += 1
        _time.sleep(0.5)

        for i, session in enumerate(sessions):
            cli_type = session.get("cli", "claude")
            sid = session.get("cli_session_id", "")
            if not sid and cli_type != "shell":
                continue
            try:
                if i > 0:
                    sock.call("surface.create", {"workspace_id": ws_id})
                    _time.sleep(0.3)
                cmd = build_resume_command(cli_type, session.get("cwd", ""), sid)
                if not cmd:
                    continue
                surfs = sock.call("surface.list", {"workspace_id": ws_id})
                surf_list = surfs if isinstance(surfs, list) else surfs.get("surfaces", [])
                if surf_list:
                    target_id = surf_list[-1].get("id", surf_list[-1].get("surface_id", ""))
                    sock.call("surface.send_text", {"surface_id": target_id, "text": cmd + "\n"})
                else:
                    raise RuntimeError("no surface found")
                restored_sessions += 1
                _time.sleep(0.5)
            except Exception as e:
                label = sid[:8] if sid else "shell"
                errors.append("session {}...: {}".format(label, e))

    return {"restored_workspaces": restored_ws, "restored_sessions": restored_sessions, "errors": errors}


def _restore_cli(snapshot):
    restored_ws = 0
    restored_sessions = 0
    errors = []

    for ws in snapshot["workspaces"]:
        sessions = ws.get("sessions", [])
        if not sessions:
            continue
        try:
            cmux_cli("new-workspace", "--name", ws["title"])
        except Exception as e:
            errors.append("workspace \"{}\": {}".format(ws["title"], e))
            continue
        restored_ws += 1
        _time.sleep(0.5)

        for i, session in enumerate(sessions):
            cli_type = session.get("cli", "claude")
            sid = session.get("cli_session_id", "")
            if not sid and cli_type != "shell":
                continue
            try:
                if i > 0:
                    cmux_cli("new-surface")
                    _time.sleep(0.3)
                cmd = build_resume_command(cli_type, session.get("cwd", ""), sid)
                if not cmd:
                    continue
                cmux_cli("send", cmd + "\n")
                restored_sessions += 1
                _time.sleep(0.5)
            except Exception as e:
                label = sid[:8] if sid else "shell"
                errors.append("session {}...: {}".format(label, e))

    return {"restored_workspaces": restored_ws, "restored_sessions": restored_sessions, "errors": errors}


# ── Snapshot info ──

def list_snapshots():
    result = []
    for label, path in [("manual", MANUAL_FILE), ("auto", AUTO_FILE)]:
        data = _load_file(path)
        if data:
            total = sum(len(w.get("sessions", [])) for w in data["workspaces"])
            result.append({
                "type": label,
                "saved_at": data["saved_at"],
                "workspaces": len(data["workspaces"]),
                "sessions": total,
            })
    return result
