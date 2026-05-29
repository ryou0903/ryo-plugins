#!/usr/bin/env python3
"""
claude-mem patch: per-directory disable (context injection + logging)

Reads a denylist file (~/.claude-mem/disabled-dirs.json). For any cwd that
equals a listed directory OR is a subdirectory of one, claude-mem will:
  - skip SessionStart "recent context" injection
  - skip all logging (observations / file-context / session-init / summarize)

This is idempotent and safe to re-run after a claude-mem update
(plugin updates overwrite worker-service.cjs, so re-run this script).

Usage:
    python3 ~/.claude-mem/patch-disabled-dirs.py
"""
import os, sys, glob, json

HOME = os.path.expanduser("~")
CACHE_GLOB = os.path.join(
    HOME, ".claude", "plugins", "cache", "thedotmack", "claude-mem", "*", "scripts", "worker-service.cjs"
)

MARKER = "__cmIsDisabledDir"

HELPERS = (
    r'function __cmDisabledDirs(){try{var f=require("fs"),p=require("path"),o=require("os");'
    r'var dir=process.env.CLAUDE_MEM_DATA_DIR||p.join(o.homedir(),".claude-mem");'
    r'var fp=p.join(dir,"disabled-dirs.json");if(!f.existsSync(fp))return[];'
    r'var raw=JSON.parse(f.readFileSync(fp,"utf-8"));'
    r'var l=Array.isArray(raw)?raw:(raw&&Array.isArray(raw.disabled)?raw.disabled:[]);'
    r'return l.map(function(s){return String(s).replace(/[\\/]+$/,"")}).filter(Boolean)}catch(e){return[]}}'
    r'function __cmIsDisabledDir(cwd){if(!cwd)return false;'
    r'var c=String(cwd).replace(/\\/g,"/").replace(/\/+$/,"");var ds=__cmDisabledDirs();'
    r'for(var i=0;i<ds.length;i++){var d=String(ds[i]).replace(/\\/g,"/");'
    r'if(c===d||c.indexOf(d+"/")===0)return true}return false}'
)

# anchors -> replacement
UM_OLD = 'function Um(t){if(process.env.CLAUDE_MEM_INTERNAL==="1")return!1;if(!t)return!0;'
UM_NEW = UM_OLD + 'if(__cmIsDisabledDir(t))return!1;'

# helpers inserted just before Um's definition (top-level scope, hoisted)
HELPERS_ANCHOR = 'function Um(t){'
HELPERS_INSERT = HELPERS + 'function Um(t){'

TX_OLD = 'TX={async execute(t){'
TX_NEW = ('TX={async execute(t){'
          'if(__cmIsDisabledDir(t.cwd??process.cwd()))'
          'return{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:""},exitCode:Et.SUCCESS};')


def patch_file(path):
    src = open(path, "r", encoding="utf-8").read()
    if MARKER in src:
        print(f"  [skip] already patched: {path}")
        return False

    # sanity: anchors must be present exactly once
    for label, anchor in (("Um", UM_OLD), ("TX", TX_OLD), ("Um-helper-anchor", HELPERS_ANCHOR)):
        n = src.count(anchor)
        if n != 1:
            print(f"  [FAIL] anchor '{label}' found {n} times (expected 1): {path}")
            return False

    backup = path + ".bak-disabled-dirs"
    if not os.path.exists(backup):
        open(backup, "w", encoding="utf-8").write(src)
        print(f"  [backup] {backup}")

    # 1) insert helpers before Um, 2) guard Um body, 3) guard TX.execute
    new = src.replace(HELPERS_ANCHOR, HELPERS_INSERT, 1)
    new = new.replace(UM_OLD, UM_NEW, 1)
    new = new.replace(TX_OLD, TX_NEW, 1)

    assert MARKER in new and UM_NEW in new and TX_NEW in new, "post-patch verification failed"
    open(path, "w", encoding="utf-8").write(new)
    print(f"  [patched] {path}")
    return True


def ensure_denylist():
    dl = os.path.join(HOME, ".claude-mem", "disabled-dirs.json")
    if os.path.exists(dl):
        print(f"  [keep] denylist exists: {dl}")
        return
    os.makedirs(os.path.dirname(dl), exist_ok=True)
    template = {
        "_comment": "List absolute directory paths. Each dir AND its subdirectories are excluded from claude-mem context injection and logging.",
        "disabled": []
    }
    open(dl, "w", encoding="utf-8").write(json.dumps(template, indent=2) + "\n")
    print(f"  [created] {dl}")


def main():
    files = sorted(glob.glob(CACHE_GLOB))
    if not files:
        print("No worker-service.cjs found under claude-mem cache.")
        return 1
    print("Patching claude-mem worker-service.cjs:")
    any_patched = False
    for f in files:
        any_patched |= patch_file(f)
    print("Denylist file:")
    ensure_denylist()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
