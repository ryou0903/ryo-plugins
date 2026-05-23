# cmux カスタムコマンド & アクション

## 設定ファイルの場所（優先順）

1. `./.cmux/cmux.json` — プロジェクトごと（最優先）
2. `./cmux.json` — フォールバック
3. `~/.config/cmux/cmux.json` — グローバル

## スキーマ構造

`cmux.json` は `actions`, `ui`, `commands` の3セクションで構成。

## アクションの種類

- `builtin` — 組み込みアクション（cmux.newTerminalなど）に別名を付ける
- `command` — シェルテキストをターミナルで実行
- `agent` — codex, claudeなどエージェント起動
- `workspaceCommand` — 名前付きワークスペース定義を実行

## アクションフィールド

- `title` — パレット/ボタン/確認に表示
- `subtitle` / `description` — パレット補助テキスト
- `keywords` — パレット検索用キーワード
- `palette` — `false` でパレット非表示
- `shortcut` — キーバインド（例: `"cmd+t"`, `["cmd+k","cmd+c"]`）
- `target` — `currentTerminal` or `newTabInCurrentPane`
- `confirm` — 実行前確認

## シンプルコマンド例

```json
{
  "actions": {
    "run-tests": {
      "title": "Run Tests",
      "keywords": ["test"],
      "command": "npm test",
      "confirm": true
    }
  }
}
```

## ワークスペースコマンド

複数ペインのカスタムレイアウトで新規ワークスペースを作成。

### フィールド
- `name` — ワークスペースタブ名
- `cwd` — 作業ディレクトリ
- `color` — タブカラー
- `layout` — ペイン配置定義（ツリー構造）

### レイアウトツリー

ツリーは**分割ノード**と**ペインノード**で構成:

- **分割ノード**: direction（horizontal/vertical）, split比率, 2つの子
- **ペインノード**: サーフェスの配列

### サーフェス定義

- `type` — `"terminal"` or `"browser"`
- `name` — カスタムタブタイトル
- `command` — 自動実行コマンド（ターミナル）
- `url` — URL（ブラウザ）
- `cwd` — 作業ディレクトリ
- `env` — 環境変数オブジェクト
- `focus` — フォーカス指定

### ワークスペースコマンド例

```json
{
  "commands": {
    "fullstack-dev": {
      "type": "workspaceCommand",
      "title": "Full-stack Dev",
      "workspaceCommand": {
        "name": "Full Stack",
        "cwd": "~/projects/myapp",
        "color": "Blue",
        "layout": {
          "type": "split",
          "direction": "horizontal",
          "split": 0.5,
          "first": {
            "type": "pane",
            "surfaces": [
              { "type": "terminal", "name": "Server", "command": "npm run dev" },
              { "type": "terminal", "name": "Shell" }
            ]
          },
          "second": {
            "type": "pane",
            "surfaces": [
              { "type": "browser", "url": "http://localhost:3000" }
            ]
          }
        }
      }
    }
  }
}
```

## UIカスタマイズ

### サーフェスタブバーボタン

`ui.surfaceTabBar.buttons` でデフォルトボタンを置き換え。
アイコン形式: `symbol`, `emoji`, `image`（相対パス対応）。

### プラスボタン制御

- `ui.newWorkspace.action` — 動作上書き
- `contextMenu` — 右クリックメニュー順序定義（アクションID, オブジェクト, セパレータ）

## 設定反映

⌘⇧, または `cmux reload-config`。スキーマエラー時はフォールバック動作し、パレットに警告表示。
