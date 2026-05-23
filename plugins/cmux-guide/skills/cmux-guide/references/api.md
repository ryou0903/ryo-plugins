# cmux API リファレンス

## Socket通信

**パス:**
- リリース: `/tmp/cmux.sock`
- デバッグ: `/tmp/cmux-debug.sock`
- 環境変数 `CMUX_SOCKET_PATH` で上書き可能

**リクエスト形式:** 改行区切りJSON
```json
{"id":"req-1","method":"workspace.list","params":{}}
```

**レスポンス形式:**
```json
{"id":"req-1","ok":true,"result":{"workspaces":[...]}}
```

**アクセスモード:**
- `off` — Socket無効
- `cmuxOnly` — cmuxターミナル内プロセスのみ
- `allowAll` — ローカルプロセス全許可

## CLIグローバルオプション

- `--socket PATH` — カスタムsocketパス
- `--json` — JSON出力
- `--window ID` — ウィンドウ指定
- `--workspace ID` — ワークスペース指定
- `--surface ID` — サーフェス指定
- `--id-format refs|uuids|both` — ID形式

---

## ワークスペース

### list-workspaces
```bash
cmux list-workspaces --json
```
Socket: `{"id":"ws-list","method":"workspace.list","params":{}}`

### new-workspace
```bash
cmux new-workspace
```
Socket: `{"id":"ws-new","method":"workspace.create","params":{}}`

### select-workspace
```bash
cmux select-workspace --workspace <id>
```
Socket: `{"id":"ws-select","method":"workspace.select","params":{"workspace_id":"<id>"}}`

### current-workspace
```bash
cmux current-workspace --json
```
Socket: `{"id":"ws-current","method":"workspace.current","params":{}}`

### close-workspace
```bash
cmux close-workspace --workspace <id>
```
Socket: `{"id":"ws-close","method":"workspace.close","params":{"workspace_id":"<id>"}}`

---

## サーフェス・ペイン

### new-split（方向: left, right, up, down）
```bash
cmux new-split right
cmux new-split down
```
Socket: `{"id":"split-new","method":"surface.split","params":{"direction":"right"}}`

### list-surfaces
```bash
cmux list-surfaces --json
```
Socket: `{"id":"surface-list","method":"surface.list","params":{}}`

### focus-surface
```bash
cmux focus-surface --surface <id>
```
Socket: `{"id":"surface-focus","method":"surface.focus","params":{"surface_id":"<id>"}}`

---

## テキスト・キー入力

### send（フォーカス中ターミナルへ）
```bash
cmux send "echo hello\n"
```
Socket: `{"id":"send-text","method":"surface.send_text","params":{"text":"echo hello\n"}}`

### send-key（enter, tab, escape, backspace, delete, up, down, left, right）
```bash
cmux send-key enter
```
Socket: `{"id":"send-key","method":"surface.send_key","params":{"key":"enter"}}`

### send-surface（特定サーフェスへ）
```bash
cmux send-surface --surface <id> "command"
```
Socket: `{"id":"send-surface","method":"surface.send_text","params":{"surface_id":"<id>","text":"command"}}`

### send-key-surface
```bash
cmux send-key-surface --surface <id> enter
```
Socket: `{"id":"send-key-surface","method":"surface.send_key","params":{"surface_id":"<id>","key":"enter"}}`

---

## 通知

### notify
```bash
cmux notify --title "Title" --body "Body"
cmux notify --title "T" --subtitle "S" --body "B"
```
Socket: `{"id":"notify","method":"notification.create","params":{"title":"Title","subtitle":"S","body":"Body"}}`

### list-notifications
```bash
cmux list-notifications --json
```
Socket: `{"id":"notif-list","method":"notification.list","params":{}}`

### clear-notifications
```bash
cmux clear-notifications
```
Socket: `{"id":"notif-clear","method":"notification.clear","params":{}}`

---

## サイドバーメタデータ

### set-status（ステータスピル）
```bash
cmux set-status build "compiling" --icon hammer --color "#ff9500" --priority 80
cmux set-status deploy "v1.2.3" --workspace workspace:2
```

### clear-status / list-status
```bash
cmux clear-status build
cmux list-status
```

### set-progress（0.0〜1.0）
```bash
cmux set-progress 0.5 --label "Building..."
cmux set-progress 1.0 --label "Done"
```

### clear-progress
```bash
cmux clear-progress
```

### log（レベル: info, progress, success, warning, error）
```bash
cmux log "Build started"
cmux log --level error --source build "Compilation failed"
cmux log --level success -- "All 42 tests passed"
```

### clear-log / list-log
```bash
cmux clear-log
cmux list-log --limit 5
```

### sidebar-state（全メタデータダンプ）
```bash
cmux sidebar-state --workspace workspace:2
```

---

## ユーティリティ

### ping
```bash
cmux ping
```
Socket: `{"id":"ping","method":"system.ping","params":{}}` → `{"pong":true}`

### capabilities
```bash
cmux capabilities --json
```
Socket: `{"id":"caps","method":"system.capabilities","params":{}}`

### identify（フォーカス中のコンテキスト）
```bash
cmux identify --json
```
Socket: `{"id":"identify","method":"system.identify","params":{}}`

### reload-config
```bash
cmux reload-config
```

---

## プログラミング例

### Python
```python
import json, os, socket

SOCKET_PATH = os.environ.get("CMUX_SOCKET_PATH", "/tmp/cmux.sock")

def rpc(method, params=None, req_id=1):
    payload = {"id": req_id, "method": method, "params": params or {}}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCKET_PATH)
        sock.sendall(json.dumps(payload).encode("utf-8") + b"\n")
        return json.loads(sock.recv(65536).decode("utf-8"))

print(rpc("workspace.list", req_id="ws"))
print(rpc("notification.create", {"title": "Hello", "body": "From Python!"}, req_id="notify"))
```

### シェルスクリプト
```bash
#!/bin/bash
SOCK="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
cmux_cmd() { printf "%s\n" "$1" | nc -U "$SOCK"; }

cmux_cmd '{"id":"ws","method":"workspace.list","params":{}}'
cmux_cmd '{"id":"notify","method":"notification.create","params":{"title":"Done","body":"Complete"}}'
```

### 通知付きビルド
```bash
#!/bin/bash
npm run build
if [ $? -eq 0 ]; then
    cmux notify --title "✓ Build Success" --body "Ready to deploy"
else
    cmux notify --title "✗ Build Failed" --body "Check the logs"
fi
```

## OSC通知（エスケープシーケンス）

### OSC 777（シンプル）
```bash
printf '\e]777;notify;My Title;Message body here\a'
```

### OSC 99（リッチ — Kittyプロトコル）
サブタイトルと通知IDをサポート。
