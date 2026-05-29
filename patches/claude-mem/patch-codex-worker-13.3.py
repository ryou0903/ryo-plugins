#!/usr/bin/env python3
"""
claude-mem Codex provider patch for v13.3.0 (atomic application, inline approach)
Adapted from patch-codex-worker.py (13.1.0) with updated minified variable names.
Usage: python3 ~/.claude-mem/patch-codex-worker-13.3.py
"""
import glob
import os
import shutil
import sys

def find_plugin_dir():
    pattern = os.path.expanduser("~/.claude/plugins/cache/thedotmack/claude-mem/*/")
    dirs = sorted(glob.glob(pattern), reverse=True)
    return dirs[0].rstrip("/") if dirs else None

# 13.3.0 variable name mapping (vs 13.1.0):
#   ke -> Pe  (SettingsDefaultsManager)
#   Wt -> Zt  (settings path)
#   W_() -> _S()  (isOpenRouterProvider)
#   pg() -> Ny()  (hasOpenRouterKey)
#   H_() -> ES()  (isGeminiProvider)
#   dg() -> Cy()  (hasGeminiKey)
#   sRt -> ujt  (openrouter URL var)

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
        'var ujt="https://openrouter.ai/api/v1/chat/completions"',
        'var ujt=(function(){try{var _s=JSON.parse(require("fs").readFileSync(require("path").join(require("os").homedir(),".claude-mem","settings.json"),"utf8"));if(_s.CLAUDE_MEM_PROVIDER==="codex"){var _p=_s.CLAUDE_MEM_CODEX_PROXY_PORT||"37780";return"http://127.0.0.1:"+_p+"/v1/chat/completions"}return _s.CLAUDE_MEM_OPENROUTER_BASE_URL||"https://openrouter.ai/api/v1/chat/completions"}catch(_e){return"https://openrouter.ai/api/v1/chat/completions"}})()',
    ),
    # P3: Add "codex" to provider validation list
    (
        "P3-validation",
        '["claude","gemini","openrouter"]',
        '["claude","gemini","openrouter","codex"]',
    ),
    # P5: getSelectedProvider - inline codex check
    (
        "P5-getSelectedProvider",
        'getSelectedProvider(){return _S()&&Ny()?"openrouter":ES()&&Cy()?"gemini":"claude"}',
        'getSelectedProvider(){return Pe.loadFromFile(Zt).CLAUDE_MEM_PROVIDER==="codex"?"codex":_S()&&Ny()?"openrouter":ES()&&Cy()?"gemini":"claude"}',
    ),
    # P6: getActiveAgent - inline codex dispatch before openrouter
    # There are two versions of getActiveAgent in 13.3.0; patch both
    (
        "P6a-getActiveAgent-verbose",
        'getActiveAgent(){if(_S()){if(Ny())return _.debug("SESSION","Using OpenRouter agent"),this.openRouterAgent;throw new Error("OpenRouter provider selected but no API key configured. Set CLAUDE_MEM_OPENROUTER_API_KEY in settings or OPENROUTER_API_KEY environment variable.")',
        'getActiveAgent(){if(Pe.loadFromFile(Zt).CLAUDE_MEM_PROVIDER==="codex"){return _.debug("SESSION","Using Codex agent via proxy"),this.openRouterAgent}if(_S()){if(Ny())return _.debug("SESSION","Using OpenRouter agent"),this.openRouterAgent;throw new Error("OpenRouter provider selected but no API key configured. Set CLAUDE_MEM_OPENROUTER_API_KEY in settings or OPENROUTER_API_KEY environment variable.")',
    ),
    (
        "P6b-getActiveAgent-compact",
        'getActiveAgent(){return _S()&&Ny()?this.openRouterAgent:ES()&&Cy()?this.geminiAgent:this.sdkAgent',
        'getActiveAgent(){return Pe.loadFromFile(Zt).CLAUDE_MEM_PROVIDER==="codex"?(_.debug("SESSION","Using Codex agent via proxy"),this.openRouterAgent):_S()&&Ny()?this.openRouterAgent:ES()&&Cy()?this.geminiAgent:this.sdkAgent',
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
        'getOpenRouterConfig(){let e=Zt,r=Pe.loadFromFile(e),n=r.CLAUDE_MEM_OPENROUTER_API_KEY',
        'getOpenRouterConfig(){let e=Zt,r=Pe.loadFromFile(e);if(r.CLAUDE_MEM_PROVIDER==="codex"){return{apiKey:r.CLAUDE_MEM_CODEX_TOKEN||"codex-via-proxy",model:r.CLAUDE_MEM_CODEX_MODEL||"gpt-5.4-mini",siteUrl:"",appName:"claude-mem-codex"}}let n=r.CLAUDE_MEM_OPENROUTER_API_KEY',
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

    with open(ws, "r") as f:
        content = f.read()

    # More specific detection: check for OUR patch markers, not generic "codex"
    is_patched = 'CLAUDE_MEM_CODEX_TOKEN' in content and 'claude-mem-codex' in content
    if is_patched:
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
