---
name: cmux-quick-notify
description: "cmuxで通知を送信する。「cmux通知送って」「cmuxで通知」「ビルド完了を通知」「cmux notify」「通知テスト」「ステータス設定」「プログレス設定」「cmux set-status」「cmux set-progress」「cmux log」のような指示で発動する。"
---

# cmux クイック通知

cmuxの通知・ステータス・プログレス・ログ機能を素早く使う。

## 通知送信

```bash
cmux notify --title "タイトル" --body "本文"
cmux notify --title "T" --subtitle "サブタイトル" --body "B"
```

OSCエスケープシーケンス（スクリプト内で便利）:
```bash
printf '\e]777;notify;タイトル;本文\a'
```

## ステータスピル

サイドバーにステータス表示:
```bash
cmux set-status <key> "テキスト" --icon <icon> --color "#hex" --priority <0-100>
cmux clear-status <key>
cmux list-status
```

例:
```bash
cmux set-status build "compiling" --icon hammer --color "#ff9500" --priority 80
cmux set-status deploy "v1.2.3" --icon rocket --color "#34c759"
```

## プログレスバー

```bash
cmux set-progress 0.0 --label "Starting..."
cmux set-progress 0.5 --label "Building..."
cmux set-progress 1.0 --label "Done"
cmux clear-progress
```

## ログ

```bash
cmux log "メッセージ"
cmux log --level info "情報"
cmux log --level success "成功"
cmux log --level warning "警告"
cmux log --level error --source build "エラー"
cmux list-log --limit 10
cmux clear-log
```

## 組み合わせ例: ビルド監視

```bash
#!/bin/bash
cmux set-status build "building" --icon hammer --color "#ff9500"
cmux set-progress 0.0 --label "Build starting..."

npm run build 2>&1 | while IFS= read -r line; do
    cmux log --source build "$line"
done

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    cmux set-progress 1.0 --label "Done"
    cmux set-status build "success" --icon checkmark --color "#34c759"
    cmux notify --title "✓ Build Success" --body "Ready to deploy"
else
    cmux clear-progress
    cmux set-status build "failed" --icon xmark --color "#ff3b30"
    cmux notify --title "✗ Build Failed" --body "Check the logs"
fi
```
