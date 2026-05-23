---
name: cmux-workspace-builder
description: "cmuxのワークスペースレイアウトを構築・設定する。「cmuxワークスペース作って」「レイアウト設定」「cmux.jsonにワークスペースコマンド追加」「フルスタック開発環境作って」「分割レイアウト定義」「ワークスペーステンプレート」「cmux workspace layout」「cmux custom command作成」「dock.json設定」「タブバーボタン設定」「cmux actions定義」のような指示で発動する。"
---

# cmux ワークスペースビルダー

cmux.jsonにワークスペースコマンドやカスタムアクションを定義し、再利用可能な開発環境レイアウトを構築する。

## 手順

1. ユーザーの要件をヒアリング（何を開発するか、必要なペイン、ブラウザが必要か等）
2. レイアウトツリーを設計
3. cmux.jsonに `commands` セクションとして書き出す
4. `cmux reload-config` で適用

## レイアウトツリー構造

ツリーは**分割ノード**と**ペインノード**で構成:

### 分割ノード
```json
{
  "type": "split",
  "direction": "horizontal",
  "split": 0.5,
  "first": { ... },
  "second": { ... }
}
```
- `direction`: `"horizontal"`（左右）or `"vertical"`（上下）
- `split`: 比率（0.0〜1.0）
- `first` / `second`: 子ノード

### ペインノード
```json
{
  "type": "pane",
  "surfaces": [
    { "type": "terminal", "name": "Editor", "command": "vim", "cwd": "~/project" },
    { "type": "browser", "url": "http://localhost:3000" }
  ]
}
```

### サーフェスフィールド
- `type` — `"terminal"` or `"browser"`
- `name` — タブタイトル
- `command` — 起動コマンド（ターミナル）
- `url` — URL（ブラウザ）
- `cwd` — 作業ディレクトリ
- `env` — 環境変数
- `focus` — `true` でフォーカス

## テンプレート集

### フルスタック開発
```json
{
  "fullstack": {
    "type": "workspaceCommand",
    "title": "Full-stack Dev",
    "keywords": ["dev", "fullstack"],
    "workspaceCommand": {
      "name": "Full Stack",
      "cwd": "~/project",
      "color": "Blue",
      "layout": {
        "type": "split",
        "direction": "horizontal",
        "split": 0.6,
        "first": {
          "type": "split",
          "direction": "vertical",
          "split": 0.7,
          "first": {
            "type": "pane",
            "surfaces": [
              { "type": "terminal", "name": "Code", "focus": true }
            ]
          },
          "second": {
            "type": "pane",
            "surfaces": [
              { "type": "terminal", "name": "Server", "command": "npm run dev" },
              { "type": "terminal", "name": "Tests", "command": "npm test -- --watch" }
            ]
          }
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
```

### Claude Code + ブラウザ
```json
{
  "claude-dev": {
    "type": "workspaceCommand",
    "title": "Claude Dev",
    "workspaceCommand": {
      "name": "Claude Dev",
      "cwd": "~/project",
      "color": "Purple",
      "layout": {
        "type": "split",
        "direction": "horizontal",
        "split": 0.5,
        "first": {
          "type": "pane",
          "surfaces": [
            { "type": "terminal", "name": "Claude", "command": "claude", "focus": true }
          ]
        },
        "second": {
          "type": "pane",
          "surfaces": [
            { "type": "browser", "url": "http://localhost:3000" },
            { "type": "terminal", "name": "Shell" }
          ]
        }
      }
    }
  }
}
```

### CI監視
```json
{
  "ci-watch": {
    "type": "workspaceCommand",
    "title": "CI Watch",
    "keywords": ["ci", "watch", "monitor"],
    "workspaceCommand": {
      "name": "CI Monitor",
      "color": "Green",
      "layout": {
        "type": "split",
        "direction": "vertical",
        "split": 0.5,
        "first": {
          "type": "pane",
          "surfaces": [
            { "type": "browser", "url": "https://github.com/org/repo/actions" }
          ]
        },
        "second": {
          "type": "pane",
          "surfaces": [
            { "type": "terminal", "name": "Logs", "command": "gh run watch" }
          ]
        }
      }
    }
  }
}
```

## 設定ファイルの場所

- グローバル: `~/.config/cmux/cmux.json`
- プロジェクト: `.cmux/cmux.json`（最優先）

設定後: `cmux reload-config` または ⌘⇧, で適用。

## 注意事項

- `cmux.json` を直接編集する前に、既存の設定をバックアップする
- ワークスペースコマンドは `commands` セクション内に配置
- `cwd` は `~` で始められる（ホームディレクトリ展開）
- レイアウトのネストは2〜3段階が実用的
