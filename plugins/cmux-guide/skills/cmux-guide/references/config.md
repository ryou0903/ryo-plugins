# cmux 設定ガイド

## 設定ファイル

### ターミナル外観（Ghostty設定）
検索順:
1. `~/.config/ghostty/config`
2. `~/Library/Application Support/com.mitchellh.ghostty/config`

```
font-family = SF Mono
font-size = 13
theme = One Dark
scrollback-limit = 50000000
split-divider-color = #3e4451
working-directory = ~/code
```

### cmux固有設定（cmux.json）
- グローバル: `~/.config/cmux/cmux.json`
- プロジェクト: `.cmux/cmux.json`（最優先）
- フォールバック: `./cmux.json`

**リロード:** ⌘⇧, または `cmux reload-config`

---

## 主要設定カテゴリ

### app（アプリ設定）

- `language` — UI言語。`"system"`, `"en"`, `"ja"`
- `appearance` — テーマ。`"light"`, `"dark"`, `"system"`
- `appIcon` — アプリアイコン。`"auto"`, `"light"`, `"dark"`
- `menuBarOnly` — Dock非表示。`true`/`false`
- `newWorkspacePlacement` — 新規WS位置。挿入位置指定
- `workspaceInheritWorkingDirectory` — ディレクトリ継承。`true`/`false`
- `minimalMode` — タイトルバー非表示。`true`/`false`
- `iMessageMode` — エージェント送信時の動作。設定値

### terminal（ターミナル設定）

- `showScrollBar` — スクロールバー表示
- `autoResumeAgentSessions` — セッション自動復帰

### browser（ブラウザ設定）

- `defaultSearchEngine` — 検索エンジン。`"Google"`, `"DuckDuckGo"`, `"Bing"`, `"Kagi"`, `"Startpage"`
- `showSearchSuggestions` — サジェスト。`true`/`false`
- `theme` — ブラウザテーマ。テーマ名
- `openTerminalLinksInCmuxBrowser` — リンク処理。`true`/`false`

### notifications（通知設定）

- Dockバッジ表示
- メニューバー表示
- カスタムサウンド
- シェルコマンド実行

### sidebar（サイドバー設定）

表示/非表示を個別制御:
- ワークスペース詳細
- Git情報
- プルリクエスト
- ポート
- SSH接続情報

### automation（オートメーション）

- ソケット制御モード（`cmuxOnly`, `allowAll`, `off`）
- Claude Code / Cursor / Gemini 統合
- ポート範囲設定

### workspaceColors（ワークスペースカラー）

16色の事前定義パレットをカスタマイズ可能。新規色も追加可。

### shortcuts.bindings

全ショートカットをカスタマイズ可能（→ shortcuts.md 参照）。

---

## 設定例

```json
{
  "app": {
    "language": "ja",
    "appearance": "dark",
    "minimalMode": false
  },
  "terminal": {
    "autoResumeAgentSessions": true
  },
  "browser": {
    "defaultSearchEngine": "Google",
    "openTerminalLinksInCmuxBrowser": true
  },
  "automation": {
    "socketMode": "cmuxOnly"
  }
}
```
