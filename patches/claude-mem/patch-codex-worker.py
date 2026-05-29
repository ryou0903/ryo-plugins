#!/usr/bin/env python3
"""
claude-mem Codex provider patch (atomic application, inline approach)
Usage: python3 ~/.claude-mem/patch-codex-worker.py
Re-run after claude-mem plugin updates.
"""
import glob
import os
import shutil
import sys

def find_plugin_dir():
    pattern = os.path.expanduser("~/.claude/plugins/cache/thedotmack/claude-mem/*/")
    dirs = sorted(glob.glob(pattern), reverse=True)
    return dirs[0].rstrip("/") if dirs else None

PATCHES = [
    # P1: Add CODEX defaults after OPENROUTER_MAX_TOKENS
    (
        "P1-defaults",
        'CLAUDE_MEM_OPENROUTER_MAX_TOKENS:"100000"',
        'CLAUDE_MEM_OPENROUTER_MAX_TOKENS:"100000",CLAUDE_MEM_OPENROUTER_BASE_URL:"",CLAUDE_MEM_CODEX_TOKEN:"",CLAUDE_MEM_CODEX_MODEL:"gpt-5.4-mini",CLAUDE_MEM_CODEX_PROXY_PORT:"37780"',
    ),
    # P2: Make OpenRouter URL dynamic (codex->proxy, else->setting or fallback)
    (
        "P2-dynamic-url",
        'var sRt="https://openrouter.ai/api/v1/chat/completions"',
        'var sRt=(function(){try{var _s=JSON.parse(require("fs").readFileSync(require("path").join(require("os").homedir(),".claude-mem","settings.json"),"utf8"));if(_s.CLAUDE_MEM_PROVIDER==="codex"){var _p=_s.CLAUDE_MEM_CODEX_PROXY_PORT||"37780";return"http://127.0.0.1:"+_p+"/v1/chat/completions"}return _s.CLAUDE_MEM_OPENROUTER_BASE_URL||"https://openrouter.ai/api/v1/chat/completions"}catch(_e){return"https://openrouter.ai/api/v1/chat/completions"}})()',
    ),
    # P3: Add "codex" to provider validation list
    (
        "P3-validation",
        '["claude","gemini","openrouter"]',
        '["claude","gemini","openrouter","codex"]',
    ),
    # P5: getSelectedProvider - inline codex check (no helper function)
    (
        "P5-getSelectedProvider",
        'getSelectedProvider(){return W_()&&pg()?"openrouter":H_()&&dg()?"gemini":"claude"}',
        'getSelectedProvider(){return ke.loadFromFile(Wt).CLAUDE_MEM_PROVIDER==="codex"?"codex":W_()&&pg()?"openrouter":H_()&&dg()?"gemini":"claude"}',
    ),
    # P6: getActiveAgent - inline codex dispatch before openrouter
    (
        "P6-getActiveAgent",
        "getActiveAgent(){if(W_()){if(pg())return",
        'getActiveAgent(){if(ke.loadFromFile(Wt).CLAUDE_MEM_PROVIDER==="codex"){return _.debug("SESSION","Using Codex agent via proxy"),this.openRouterAgent}if(W_()){if(pg())return',
    ),
    # P7: startGeneratorWithProvider ternary - map codex to openRouterAgent
    (
        "P7-ternary",
        'n==="openrouter"?this.openRouterAgent:n==="gemini"?this.geminiAgent:this.sdkAgent,o=n==="openrouter"?"OpenRouter":n==="gemini"?"Gemini":"Claude SDK"',
        'n==="openrouter"||n==="codex"?this.openRouterAgent:n==="gemini"?this.geminiAgent:this.sdkAgent,o=n==="codex"?"Codex":n==="openrouter"?"OpenRouter":n==="gemini"?"Gemini":"Claude SDK"',
    ),
    # P8: getOpenRouterConfig - override for codex
    (
        "P8-config-override",
        "getOpenRouterConfig(){let e=Wt,r=ke.loadFromFile(e),n=r.CLAUDE_MEM_OPENROUTER_API_KEY",
        'getOpenRouterConfig(){let e=Wt,r=ke.loadFromFile(e);if(r.CLAUDE_MEM_PROVIDER==="codex"){return{apiKey:r.CLAUDE_MEM_CODEX_TOKEN||"codex-via-proxy",model:r.CLAUDE_MEM_CODEX_MODEL||"gpt-5.4-mini",siteUrl:"",appName:"claude-mem-codex"}}let n=r.CLAUDE_MEM_OPENROUTER_API_KEY',
    ),
]

def main():
    plugin_dir = find_plugin_dir()
    if not plugin_dir:
        print("ERROR: claude-mem plugin directory not found")
        sys.exit(1)

    ws = os.path.join(plugin_dir, "scripts", "worker-service.cjs")
    if not os.path.exists(ws):
        print(f"ERROR: {ws} not found")
        sys.exit(1)

    print(f"Target: {ws}")
    print(f"Plugin: {os.path.basename(plugin_dir)}")

    backup = ws + ".bak-codex"

    # If already patched, restore from backup first for clean re-application
    with open(ws, "r") as f:
        content = f.read()

    if 'CLAUDE_MEM_CODEX_TOKEN' in content or '"codex"' in content:
        if os.path.exists(backup):
            print("Already patched. Restoring from backup for clean re-application...")
            shutil.copy2(backup, ws)
            with open(ws, "r") as f:
                content = f.read()
        else:
            print("Already patched but no backup found. Cannot safely re-apply.")
            sys.exit(1)

    # Create backup if it doesn't exist
    if not os.path.exists(backup):
        shutil.copy2(ws, backup)
        print(f"Backup: {backup}")
    else:
        print(f"Backup exists: {backup}")

    # Validate all patterns exist BEFORE any replacement
    print("\nValidating patterns...")
    for name, search, _ in PATCHES:
        count = content.count(search)
        if count == 0:
            print(f"  FAIL {name}: pattern not found")
            sys.exit(1)
        if count > 1 and name not in ("P3-validation",):
            print(f"  WARN {name}: {count} occurrences (expected 1)")
        else:
            print(f"  OK   {name}")

    # Apply all patches
    print("\nApplying patches...")
    for name, search, replace in PATCHES:
        if name == "P3-validation":
            content = content.replace(search, replace)
        else:
            content = content.replace(search, replace, 1)
        print(f"  Applied {name}")

    # Post-validation
    print("\nVerifying...")
    checks = [
        ("codex in validation", '"codex"'),
        ("getSelectedProvider codex", 'CLAUDE_MEM_PROVIDER==="codex"?"codex"'),
        ("getActiveAgent codex", "Using Codex agent via proxy"),
        ("ternary codex", 'n==="codex"?"Codex"'),
        ("config override", "claude-mem-codex"),
        ("dynamic URL", "CLAUDE_MEM_CODEX_PROXY_PORT"),
        ("codex defaults", "CLAUDE_MEM_CODEX_TOKEN"),
    ]
    all_ok = True
    for label, pattern in checks:
        if pattern in content:
            print(f"  OK   {label}")
        else:
            print(f"  FAIL {label}")
            all_ok = False

    if not all_ok:
        print("\nVerification failed. Restoring backup.")
        shutil.copy2(backup, ws)
        sys.exit(1)

    # Write
    with open(ws, "w") as f:
        f.write(content)

    print(f"\nAll {len(PATCHES)} patches applied successfully.")
    print("Restart the worker to apply: kill the worker PID, then restart the session.")

if __name__ == "__main__":
    main()
