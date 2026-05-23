# cmux コンセプト — 階層構造

cmuxは **Window → Workspace → Pane → Surface → Panel** の5階層で構成される。

## Window（ウィンドウ）
- macOSネイティブウィンドウ
- ⌘⇧N で複数ウィンドウを開ける
- 各ウィンドウは独立したサイドバーを持つ

## Workspace（ワークスペース）
- サイドバーの1項目 = 1ワークスペース
- 1つ以上の分割ペインを含む
- Socket APIでは `workspace`、環境変数 `CMUX_WORKSPACE_ID`
- ⌘N（新規）、⌘1–9（ジャンプ）、⌘P（スイッチャー）

## Pane（ペイン）
- ワークスペース内の分割領域
- ⌘D（右分割）、⌘⇧D（下分割）
- 複数のサーフェスを保持できる

## Surface（サーフェス）
- ペイン内のタブ = 個々のターミナルまたはブラウザセッション
- 環境変数 `CMUX_SURFACE_ID` を持つ
- ⌘T で新規作成

## Panel（パネル）
- サーフェス内の実コンテンツ
- ターミナル（Ghostty）またはWebビューの2種類
- 主に内部概念

## 環境変数（自動設定）

- `CMUX_WORKSPACE_ID` — 現在のワークスペースID
- `CMUX_SURFACE_ID` — 現在のサーフェスID
- `CMUX_SOCKET_PATH` — socketパス（上書き用）
- `TERM_PROGRAM` — `ghostty`
- `TERM` — `xterm-ghostty`

## cmux検出（スクリプト用）

```bash
# cmux管理ターミナル内かどうか
[ -n "${CMUX_WORKSPACE_ID:-}" ] && [ -n "${CMUX_SURFACE_ID:-}" ] && echo "Inside cmux"

# socketが使えるか
SOCK="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
[ -S "$SOCK" ] && echo "Socket available"

# 通常Ghosttyとの区別
[ "$TERM_PROGRAM" = "ghostty" ] && [ -n "${CMUX_WORKSPACE_ID:-}" ] && echo "In cmux"
```
