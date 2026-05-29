#!/bin/bash
# claude-mem Codex provider patch (worker + UI)
# Usage: bash ~/.claude-mem/patch-codex.sh
# Re-run after claude-mem plugin updates
# Supports: 13.1.x, 13.3.x+
set -euo pipefail

PLUGIN_DIR=$(ls -dt "$HOME/.claude/plugins/cache/thedotmack/claude-mem"/[0-9]*/ 2>/dev/null | head -1)
if [ -z "$PLUGIN_DIR" ]; then
  echo "ERROR: claude-mem plugin directory not found"
  exit 1
fi

VERSION=$(basename "$PLUGIN_DIR")
MAJOR_MINOR=$(echo "$VERSION" | cut -d. -f1,2)

echo "=== claude-mem Codex Patch ==="
echo "Plugin: $VERSION"
echo ""

# --- Detect UI component variable name per version ---
# 13.1.x uses "At", 13.3.x+ uses "Ot"
detect_ui_component_var() {
  local vb="$1"
  if grep -q 'S.default.createElement(Ot,{label:"Worker Port"' "$vb" 2>/dev/null; then
    echo "Ot"
  elif grep -q 'S.default.createElement(At,{label:"Worker Port"' "$vb" 2>/dev/null; then
    echo "At"
  else
    echo ""
  fi
}

# --- Worker patch (Python, atomic) ---
echo "--- Worker Service ---"
case "$MAJOR_MINOR" in
  13.1)
    python3 ~/.claude-mem/patch-codex-worker.py
    ;;
  13.3|13.4|13.5|13.6|13.7|13.8|13.9|14.*|15.*)
    if [ -f ~/.claude-mem/patch-codex-worker-13.3.py ]; then
      python3 ~/.claude-mem/patch-codex-worker-13.3.py
    else
      echo "ERROR: patch-codex-worker-13.3.py not found"
      exit 1
    fi
    ;;
  *)
    echo "ERROR: Unsupported version $VERSION"
    echo "You may need to create a new patcher for this version."
    echo "Check minified variable names with:"
    echo "  grep -oP 'getSelectedProvider\\(\\)\\{[^}]{0,300}' \"\$PLUGIN_DIR/scripts/worker-service.cjs\""
    exit 1
    ;;
esac

# --- UI patch ---
echo ""
echo "--- Viewer Bundle ---"
VB="$PLUGIN_DIR/ui/viewer-bundle.js"

if [ ! -f "$VB" ]; then
  echo "ERROR: $VB not found"
  exit 1
fi

if grep -q 'Codex (ChatGPT Pro)' "$VB" 2>/dev/null; then
  echo "UI already patched. Skipping."
else
  COMP_VAR=$(detect_ui_component_var "$VB")
  if [ -z "$COMP_VAR" ]; then
    echo "ERROR: Cannot detect UI component variable (At/Ot). Unknown version layout."
    exit 1
  fi
  echo "Detected UI component var: $COMP_VAR"

  cp "$VB" "$VB.bak-codex"
  echo "Backup: $VB.bak-codex"

  python3 -c "
import sys

comp = '$COMP_VAR'

with open('$VB', 'r') as f:
    content = f.read()

# V1: Add Codex to provider dropdown
old1 = 'value:\"openrouter\"},\"OpenRouter (multi-model)\"))),i.CLAUDE_MEM_PROVIDER===\"claude\"'
new1 = 'value:\"openrouter\"},\"OpenRouter (multi-model)\"),S.default.createElement(\"option\",{value:\"codex\"},\"Codex (ChatGPT Pro)\"))),i.CLAUDE_MEM_PROVIDER===\"claude\"'
if old1 not in content:
    print('V1: FAIL - pattern not found'); sys.exit(1)
content = content.replace(old1, new1, 1)
print('  Applied V1 (dropdown)')

# V2: Add Codex settings section (component var is version-dependent)
old2 = f'placeholder:\"claude-mem\"}})))),S.default.createElement({comp},{{label:\"Worker Port\"'
new2 = f'placeholder:\"claude-mem\"}})))),i.CLAUDE_MEM_PROVIDER===\"codex\"&&S.default.createElement(S.default.Fragment,null,S.default.createElement({comp},{{label:\"Codex Model\",tooltip:\"GPT model for generating observations via ChatGPT Pro\"}},S.default.createElement(\"select\",{{value:i.CLAUDE_MEM_CODEX_MODEL||\"gpt-5.4-mini\",onChange:m=>o(\"CLAUDE_MEM_CODEX_MODEL\",m.target.value)}},S.default.createElement(\"option\",{{value:\"gpt-5.4-mini\"}},\"GPT-5.4 Mini (fastest)\"),S.default.createElement(\"option\",{{value:\"gpt-5.4\"}},\"GPT-5.4 (balanced)\"),S.default.createElement(\"option\",{{value:\"gpt-5.5\"}},\"GPT-5.5 (highest quality)\"))),S.default.createElement({comp},{{label:\"Access Token\",tooltip:\"Your ChatGPT Pro access_token (eyJ...) from Codex. Expires periodically.\"}},S.default.createElement(\"input\",{{type:\"password\",value:i.CLAUDE_MEM_CODEX_TOKEN||\"\",onChange:m=>o(\"CLAUDE_MEM_CODEX_TOKEN\",m.target.value),placeholder:\"eyJ...\"}})),S.default.createElement({comp},{{label:\"Proxy Port\",tooltip:\"Local proxy port for Codex bridge (default: 37780)\"}},S.default.createElement(\"input\",{{type:\"text\",value:i.CLAUDE_MEM_CODEX_PROXY_PORT||\"37780\",onChange:m=>o(\"CLAUDE_MEM_CODEX_PROXY_PORT\",m.target.value),placeholder:\"37780\"}}))),S.default.createElement({comp},{{label:\"Worker Port\"'
if old2 not in content:
    print(f'V2: FAIL - pattern not found (tried component var: {comp})')
    sys.exit(1)
content = content.replace(old2, new2, 1)
print('  Applied V2 (settings section)')

with open('$VB', 'w') as f:
    f.write(content)
print('  UI patches: OK')
"
fi

# --- Validation ---
echo ""
echo "--- Final Validation ---"
WS="$PLUGIN_DIR/scripts/worker-service.cjs"
PASS=true
grep -q 'CLAUDE_MEM_CODEX_TOKEN' "$WS" || { echo "FAIL: defaults"; PASS=false; }
grep -q 'claude-mem-codex' "$WS" || { echo "FAIL: config override"; PASS=false; }
grep -q 'Using Codex agent via proxy' "$WS" || { echo "FAIL: agent dispatch"; PASS=false; }
grep -q '"codex"' "$WS" || { echo "FAIL: codex strings"; PASS=false; }
grep -q 'Codex (ChatGPT Pro)' "$VB" || { echo "FAIL: UI dropdown"; PASS=false; }
grep -q 'CLAUDE_MEM_CODEX_MODEL' "$VB" || { echo "FAIL: UI settings"; PASS=false; }

if $PASS; then
  echo "All patches verified."
  echo ""
  echo "Restart the worker: kill the worker PID, then restart the session."
else
  echo "Some patches failed!"
  exit 1
fi
