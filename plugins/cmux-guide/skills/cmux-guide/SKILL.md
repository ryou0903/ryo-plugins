---
name: cmux-guide
description: "cmuxターミナルマルチプレクサの使い方・機能・設定・API・ショートカットについての質問に答える。「cmuxの使い方」「cmuxのショートカット」「cmuxのAPI」「cmux設定」「ワークスペースの作り方」「サーフェスとは」「cmux通知」「cmuxブラウザ」「cmux SSH」「cmux Dock」「cmux セッション復元」「カスタムコマンド」「cmux browser」「cmux notify」「cmux.json」「dock.json」「cmux split」「cmux how to」「cmuxのコンセプト」「cmux チェンジログ」「cmux 更新履歴」「cmux changelog」「cmux 新機能」「cmux アップデート」のような質問で発動する。"
---

# cmux ガイド

cmux（Ghosttyベースの軽量ネイティブmacOSターミナル）の包括的リファレンス。複数AIコーディングエージェント管理向けに設計されており、縦タブ、通知パネル、Socketベース制御APIを備える。

## 対応トピック

ユーザーの質問に応じて、以下のリファレンスを参照して回答する:

- 階層構造・コンセプト（Window/Workspace/Pane/Surface/Panel） → `references/concepts.md`
- CLI・Socket API → `references/api.md`
- キーボードショートカット → `references/shortcuts.md`
- cmux.json・Ghostty設定 → `references/config.md`
- カスタムコマンド・アクション・ワークスペースコマンド → `references/custom-commands.md`
- 通知システム → `references/notifications.md`
- ブラウザ自動化 → `references/browser.md`
- SSH → `references/ssh.md`
- セッション復元 → `references/session-restore.md`
- Dock → `references/dock.md`
- チェンジログ・更新履歴・新機能 → WebFetchで `https://cmux.com/ja/docs/changelog` を取得して回答

## 回答ルール

1. まずユーザーの質問に最も関連するリファレンスファイルを特定し、その内容を読んで回答する
2. **チェンジログ/更新履歴/新機能**に関する質問は、ローカルリファレンスではなく `https://cmux.com/ja/docs/changelog` をWebFetchで取得して最新情報を回答する
3. 具体的なコマンド例・設定例・ショートカットを含めて実用的に回答する
4. CLIとSocket APIの両方がある場合は両方示す
5. 日本語で回答する

## クイックリファレンス

### 基本操作
- ワークスペース: ⌘N（新規）、⌘1-9（切替）、⌘P（スイッチャー）
- サーフェス: ⌘T（新規）、⌃1-9（切替）
- 分割: ⌘D（右）、⌘⇧D（下）、⌥⌘D（右にブラウザ）
- 通知: ⌘⇧I（パネル）、⌘⇧U（未読へジャンプ）
- 設定リロード: ⌘⇧,

### 設定ファイル
- Ghostty: `~/.config/ghostty/config`
- cmux: `~/.config/cmux/cmux.json`（グローバル）、`.cmux/cmux.json`（プロジェクト）
- Dock: `~/.config/cmux/dock.json`（グローバル）、`.cmux/dock.json`（プロジェクト）

### Socket
- パス: `/tmp/cmux.sock`
- 環境変数: `CMUX_SOCKET_PATH`, `CMUX_WORKSPACE_ID`, `CMUX_SURFACE_ID`

### よく使うCLIコマンド
```bash
cmux list-workspaces --json    # ワークスペース一覧
cmux new-workspace              # 新規作成
cmux new-split right            # 右に分割
cmux send "command\n"           # テキスト送信
cmux notify --title "T" --body "B"  # 通知
cmux set-status key "value"     # ステータスピル
cmux set-progress 0.5           # プログレスバー
cmux identify --json            # 現在のコンテキスト
cmux ping                       # 疎通確認
```
