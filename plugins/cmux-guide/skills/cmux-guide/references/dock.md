# cmux Dock

右サイドバーにTUIコントロールを追加する機能。JSONで定義したコマンドがGhosttyベースの専用ターミナルセクションとして表示される。

## 設定ファイル（優先順）

1. `.cmux/dock.json` — リポジトリ（プロジェクト）
2. `~/.config/cmux/dock.json` — グローバル

## dock.json フィールド

- `id` — 安定した一意ID（短く、再利用しない）
- `title` — Dockヘッダーのラベル
- `command` — ログインシェル内で起動するコマンド
- `cwd` — 作業ディレクトリ（相対パスはプロジェクトルートから解決）
- `height` — 高さ（未指定なら残りスペースを共有）
- `env` — そのコントロール限定の環境変数

## 設定例

```json
[
  {
    "id": "logs",
    "title": "App Logs",
    "command": "tail -f /var/log/app.log",
    "height": 10
  },
  {
    "id": "git-status",
    "title": "Git Status",
    "command": "watch -n 5 git status --short"
  },
  {
    "id": "dev-server",
    "title": "Dev Server",
    "command": "npm run dev",
    "cwd": "./frontend"
  }
]
```

## チーム共有方針

- リポジトリ固有: `.cmux/dock.json` にコミット
- 個人用: `~/.config/cmux/dock.json`（ソース管理外）
- シークレット不可: シェルやenvファイルから読み込む
