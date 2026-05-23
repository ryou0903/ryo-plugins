---
name: env-capture
description: "Capture and register environment information (tools, services, commands, URLs, MCP servers, plugins, skills) into the env-registry database. Triggers when: a new tool/service/plugin is installed or mentioned; a URL, port, or command comes up in conversation; user says 'remember this', 'register this', 'save this to env'; or existing registry info needs updating. Also triggers when environment changes are detected (version upgrades, uninstalls, config changes). Covers all of Ryo's devices: Mac, Windows, Galaxy."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(cat:*)
---

# env-capture

環境情報を `~/.claude/env-registry/` に登録・更新するスキル。

## 手順

1. **ガイドライン読込**: `${CLAUDE_PLUGIN_ROOT}/reference/guideline.md` を読む
2. **INDEX確認**: `~/.claude/env-registry/INDEX.md` を読み、既存エントリを確認
3. **ガイドラインに従って書く**: フォーマット・カテゴリ配置・命名規則はすべてガイドラインに記載済み

## 新規 vs 更新 vs 廃止

- **新規**: カテゴリフォルダにファイル作成 → INDEX.mdにポインタ追加
- **更新**: 変更フィールドのみ編集 → `updated:` を今日の日付に → INDEX.mdのサマリも必要なら更新
- **廃止**: `status: deprecated` に変更 → noteに理由追記 → INDEX.md更新

## 出力

一文で報告。例: "env-registry: claude-mem を plugins/ に登録した（コマンド3件、URL1件）"
