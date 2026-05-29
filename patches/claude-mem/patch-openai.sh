#!/bin/bash
# claude-mem OpenAI API patch
# Usage: bash ~/.claude-mem/patch-openai.sh
# Run after claude-mem plugin updates to re-apply the patch

PLUGIN_DIR=$(ls -dt "$HOME/.claude/plugins/cache/thedotmack/claude-mem"/[0-9]*/ 2>/dev/null | head -1)
TARGET="$PLUGIN_DIR/scripts/worker-service.cjs"

if [ ! -f "$TARGET" ]; then
  echo "ERROR: worker-service.cjs not found at $TARGET"
  exit 1
fi

if grep -q 'CLAUDE_MEM_OPENROUTER_BASE_URL' "$TARGET"; then
  echo "Already patched."
  exit 0
fi

cp "$TARGET" "$TARGET.bak"

sed -i '' 's|var abe="https://openrouter.ai/api/v1/chat/completions"|var abe=(function(){try{var _s=JSON.parse(require("fs").readFileSync(require("path").join(require("os").homedir(),".claude-mem","settings.json"),"utf8"));return _s.CLAUDE_MEM_OPENROUTER_BASE_URL\|\|"https://openrouter.ai/api/v1/chat/completions"}catch(_e){return"https://openrouter.ai/api/v1/chat/completions"}})()|' "$TARGET"

if grep -q 'CLAUDE_MEM_OPENROUTER_BASE_URL' "$TARGET"; then
  echo "Patch applied successfully to $TARGET"
else
  echo "ERROR: Patch failed. Restoring backup."
  cp "$TARGET.bak" "$TARGET"
  exit 1
fi
