# cmux 通知システム

## ライフサイクル

1. **受信** — パネルに表示、デスクトップアラート発火（抑制されていなければ）
2. **未読** — ワークスペースタブにバッジ表示
3. **既読** — そのワークスペースを表示するとクリア
4. **クリア済み** — パネルから削除

## アラート抑制条件

- cmuxウィンドウにフォーカスがある
- 通知を送信したワークスペースがアクティブ
- 通知パネルが開いている

## 通知パネル操作

- `⌘⇧I` — 通知パネルを開く
- `クリック` — そのワークスペースにジャンプ
- `⌘⇧U` — 最新未読ワークスペースへ直接ジャンプ

## 送信方法

### CLI
```bash
cmux notify --title "Task Complete" --body "Your build finished"
cmux notify --title "T" --subtitle "S" --body "B"
```

### OSC 777（シンプル）
```bash
printf '\e]777;notify;My Title;Message body here\a'
```

### OSC 99（リッチ — Kittyプロトコル）
サブタイトルと通知IDをサポート。

### Socket API
```json
{"id":"notify","method":"notification.create","params":{"title":"Title","body":"Body"}}
```

## カスタムコマンド実行

通知スケジュール時にシェルコマンド実行可能。環境変数:
- `CMUX_NOTIFICATION_TITLE`
- `CMUX_NOTIFICATION_SUBTITLE`
- `CMUX_NOTIFICATION_BODY`

## 通知フック（cmux.json）

JSON形式の入出力で以下を制御:
- バナーのフィルタリング
- サイドバー履歴の保持/スキップ
- サウンド実行
- 後続フックの停止

## エージェント連携

### Claude Code
フックスクリプトで `Stop` と `PostToolUse` イベントで通知。

### GitHub Copilot CLI
ライフサイクルイベント対応:
- `userPromptSubmitted`
- `agentStop`
- `errorOccurred`
- `sessionEnd`

## 通知付きビルドスクリプト例

```bash
#!/bin/bash
npm run build
if [ $? -eq 0 ]; then
    cmux notify --title "✓ Build Success" --body "Ready to deploy"
else
    cmux notify --title "✗ Build Failed" --body "Check the logs"
fi
```
