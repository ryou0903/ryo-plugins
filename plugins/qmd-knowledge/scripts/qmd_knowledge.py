#!/usr/bin/env python3
"""QMD CLI wrappers for Claude Code knowledge search and fetch."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


QMD_COMMAND = Path("/Users/ryo/.local/bin/qmd-node22")
QMD_CONFIG_HOME = Path("/Users/ryo/.claude/qmd/config")
QMD_CACHE_HOME = Path("/Users/ryo/.claude/qmd/cache")
DEFAULT_RESULT_LIMIT = 5
DEFAULT_GET_LINES = 40
MAX_GET_LINES = 200


class QmdError(RuntimeError):
    pass


@dataclass(frozen=True)
class QmdContext:
    qmd_command: Path
    config_home: Path
    cache_home: Path
    collection_roots: dict[str, Path]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search and read knowledge through QMD."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("search", help="Run QMD vsearch.")
    sp.add_argument("query")
    sp.add_argument("--max-results", type=int, default=DEFAULT_RESULT_LIMIT)
    sp.add_argument("--path-filter")
    sp.add_argument("--min-score", type=float)
    sp.add_argument("--collection")

    qp = sub.add_parser("query", help="Run QMD hybrid query.")
    qp.add_argument("query")
    qp.add_argument("--max-results", type=int, default=DEFAULT_RESULT_LIMIT)
    qp.add_argument("--strategy", choices=["balanced", "auto"], default="balanced")
    qp.add_argument("--candidate-limit", type=int, default=15)
    qp.add_argument("--path-filter")
    qp.add_argument("--min-score", type=float)
    qp.add_argument("--collection")

    gp = sub.add_parser("get", help="Read a document slice.")
    gp.add_argument("path")
    gp.add_argument("--line", type=int)
    gp.add_argument("--lines", type=int, default=DEFAULT_GET_LINES)

    return parser


def build_context() -> QmdContext:
    if not QMD_COMMAND.exists():
        raise QmdError(f"QMD command not found: {QMD_COMMAND}")

    index_path = QMD_CONFIG_HOME / "qmd" / "index.yml"
    cache_index = QMD_CACHE_HOME / "qmd" / "index.sqlite"

    if not index_path.exists():
        raise QmdError(f"QMD index config not found: {index_path}")
    if not cache_index.exists():
        raise QmdError(f"QMD cache index not found: {cache_index}")

    collection_roots = parse_index(index_path)
    return QmdContext(
        qmd_command=QMD_COMMAND,
        config_home=QMD_CONFIG_HOME,
        cache_home=QMD_CACHE_HOME,
        collection_roots=collection_roots,
    )


def parse_index(index_path: Path) -> dict[str, Path]:
    collections: dict[str, Path] = {}
    current: str | None = None
    for raw in index_path.read_text().splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line == "collections:":
            continue
        if line.startswith("  ") and line.endswith(":") and not line.startswith("    "):
            current = line.strip().rstrip(":")
            continue
        if current and line.startswith("    path:"):
            path_value = line.split(":", 1)[1].strip()
            collections[current] = Path(path_value)
    if not collections:
        raise QmdError(f"No collections found in {index_path}")
    return collections


def run_qmd(ctx: QmdContext, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(ctx.config_home)
    env["XDG_CACHE_HOME"] = str(ctx.cache_home)
    return subprocess.run(
        [str(ctx.qmd_command), *args],
        capture_output=True, text=True, env=env, check=False,
    )


def extract_json_array(stdout: str) -> list[dict[str, Any]]:
    start = stdout.find("[")
    end = stdout.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise QmdError(f"Expected JSON array, got:\n{stdout.strip()}")
    payload = json.loads(stdout[start : end + 1])
    if not isinstance(payload, list):
        raise QmdError("QMD output was not a JSON array.")
    return payload


def parse_qmd_uri(uri: str) -> tuple[str, str]:
    prefix = "qmd://"
    if not uri.startswith(prefix):
        raise QmdError(f"Unsupported document reference: {uri}")
    remainder = uri[len(prefix):]
    if "/" not in remainder:
        raise QmdError(f"Malformed document reference: {uri}")
    collection, rel = remainder.split("/", 1)
    if not collection or not rel:
        raise QmdError(f"Malformed document reference: {uri}")
    return collection, rel


def resolve_uri(ctx: QmdContext, uri: str) -> Path:
    collection, rel = parse_qmd_uri(uri)
    root = ctx.collection_roots.get(collection)
    if root is None:
        raise QmdError(f"Unknown collection '{collection}'.")
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        raise QmdError(f"Path escaped allowed root: {uri}")
    return candidate


def clean_snippet(snippet: str) -> str:
    lines = [l for l in snippet.splitlines() if not l.startswith("@@ ")]
    return "\n".join(lines).strip()


def matches_filter(needle: str, abs_path: Path, uri: str, root: Path) -> bool:
    n = needle.strip().lower()
    if not n:
        return True
    try:
        rel = str(abs_path.relative_to(root)).lower()
    except ValueError:
        rel = abs_path.name.lower()
    return any(n in h for h in [str(abs_path).lower(), uri.lower(), rel])


def format_results(ctx: QmdContext, raw: list[dict[str, Any]], args: argparse.Namespace, backend: str) -> dict[str, Any]:
    results = []
    path_filter = getattr(args, "path_filter", None)
    for item in raw:
        uri = str(item.get("file", "")).strip()
        if not uri:
            continue
        abs_path = resolve_uri(ctx, uri)
        collection, _ = parse_qmd_uri(uri)
        root = ctx.collection_roots[collection]
        if path_filter and not matches_filter(path_filter, abs_path, uri, root):
            continue
        results.append({
            "path": str(abs_path),
            "sourceUri": uri,
            "collection": collection,
            "score": item.get("score"),
            "title": item.get("title") or abs_path.name,
            "snippet": clean_snippet(str(item.get("snippet", ""))),
        })

    meta: dict[str, Any] = {
        "backend": backend,
        "resultCount": len(results),
        "pathFilter": path_filter,
        "minScore": getattr(args, "min_score", None),
        "qmdCommand": str(ctx.qmd_command),
    }
    if hasattr(args, "strategy"):
        meta["queryStrategy"] = args.strategy
        meta["candidateLimit"] = args.candidate_limit

    return {"query": args.query, "results": results, "meta": meta}


def cmd_search(args: argparse.Namespace) -> dict[str, Any]:
    ctx = build_context()
    qmd_args = ["vsearch", args.query, "-n", str(args.max_results), "--json"]
    if args.min_score is not None:
        qmd_args.extend(["--min-score", str(args.min_score)])
    if args.collection:
        qmd_args.extend(["-c", args.collection])

    r = run_qmd(ctx, qmd_args)
    if r.returncode != 0:
        raise QmdError((r.stderr or r.stdout).strip() or "QMD vsearch failed.")
    return format_results(ctx, extract_json_array(r.stdout), args, "qmd-vsearch")


def cmd_query(args: argparse.Namespace) -> dict[str, Any]:
    ctx = build_context()
    if args.strategy == "balanced":
        query_text = f"lex: {args.query}\nvec: {args.query}"
    else:
        query_text = args.query

    qmd_args = ["query", query_text, "-n", str(args.max_results), "--json", "-C", str(args.candidate_limit)]
    if args.min_score is not None:
        qmd_args.extend(["--min-score", str(args.min_score)])
    if args.collection:
        qmd_args.extend(["-c", args.collection])

    r = run_qmd(ctx, qmd_args)
    if r.returncode != 0:
        raise QmdError((r.stderr or r.stdout).strip() or "QMD query failed.")
    return format_results(ctx, extract_json_array(r.stdout), args, "qmd-query")


def cmd_get(args: argparse.Namespace) -> dict[str, Any]:
    ctx = build_context()
    lines = args.lines
    if lines < 1 or lines > MAX_GET_LINES:
        raise QmdError(f"--lines must be between 1 and {MAX_GET_LINES}.")
    line = args.line if args.line is not None else 1
    if line < 1:
        raise QmdError("--line must be at least 1.")

    target = args.path
    if target.startswith("qmd://"):
        resolve_uri(ctx, target)
    else:
        candidate = Path(target).expanduser()
        if candidate.is_absolute():
            resolved = candidate.resolve()
            if not any(
                True
                for root in ctx.collection_roots.values()
                if _within(resolved, root.resolve())
            ):
                raise QmdError(f"Path outside allowed roots: {target}")
            target = str(resolved)
        else:
            raise QmdError(f"Use absolute path or qmd:// URI: {target}")

    r = run_qmd(ctx, ["get", f"{target}:{line}", "-l", str(lines)])
    if r.returncode != 0:
        raise QmdError((r.stderr or r.stdout).strip() or "QMD get failed.")

    content = r.stdout.rstrip("\n")
    content_lines = content.splitlines() if content else []
    resolved_path = str(resolve_uri(ctx, target)) if target.startswith("qmd://") else target

    return {
        "path": resolved_path,
        "startLine": line,
        "endLine": line + max(len(content_lines) - 1, 0),
        "content": content,
        "truncated": len(content_lines) >= lines,
        "meta": {
            "backend": "qmd-get",
            "requestedLines": lines,
            "qmdCommand": str(ctx.qmd_command),
        },
    }


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "search":
            payload = cmd_search(args)
        elif args.command == "query":
            payload = cmd_query(args)
        elif args.command == "get":
            payload = cmd_get(args)
        else:
            raise QmdError(f"Unknown command: {args.command}")
    except QmdError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
