---
name: env-search
description: "env-registryからツール・コマンド・サービス情報を検索する。「adbの使い方」「ポート37777は何」「gws コマンド一覧」「インストール済みCLI」のように自然言語で聞ける。env-registryの中身を探す、コマンドを思い出したい、ツールの情報を確認したい時に使う。"
allowed-tools: Read, Glob, Grep, Bash(ls:*), Bash(cat:*)
---

# env-search

`~/.claude/env-registry/` を検索して関連エントリを返す読み取り専用スキル。

## 検索手順

1. `~/.claude/env-registry/INDEX.md` を読む
2. ユーザーのクエリに合致しそうなエントリを特定（名前・サマリから判断）
3. 候補が不明確なら `Grep` で `~/.claude/env-registry/` 全体をキーワード検索
4. マッチしたエントリファイルを `Read` して内容を返す

## 検索対象

- エントリ名・tags（frontmatter）
- コマンド名・URL・パス（body内テーブル）
- purpose・notes（本文）

## 出力

- 該当エントリが1件: 内容をそのまま表示
- 該当エントリが複数: 各エントリのpurposeとcommands概要を一覧表示
- 該当なし: 「env-registryに該当エントリなし」と報告

日本語で回答。技術識別子はそのまま英語。
