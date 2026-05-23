---
name: env-check
description: "env-registryのエントリを実環境と照合し、整合性を検証する。バージョンのずれ、未インストール、パス不在を検出。「環境チェック」「registryの整合性確認」「古いエントリない？」「env-check」で発動。"
allowed-tools: Read, Glob, Grep, Bash(which:*), Bash(ls:*), Bash(cat:*), Bash(*--version*), Bash(*-v*), Bash(*version*), Edit
---

# env-check

`~/.claude/env-registry/` のエントリを実環境と突き合わせて検証するスキル。

## 検証手順

1. `~/.claude/env-registry/INDEX.md` を読み、全エントリを列挙
2. 各エントリのfrontmatterから `status`, `version`, `category` を取得
3. カテゴリ別に検証:

### clis
- `which <command>` でインストール確認
- `<command> --version` でバージョン照合
- PATHに通っているか確認

### services
- 設定ファイル・ディレクトリの存在確認
- ポートがlistenしているか（オプション）

### plugins / skills
- プラグインディレクトリの存在確認

### platforms
- OS情報との照合（`sw_vers` など）

## 不整合の報告

テーブル形式で報告:

| Entry | Issue | Current | Registry |
|---|---|---|---|
| android-sdk | バージョン不一致 | 1.0.42 | 1.0.41 |
| gws | 未インストール | not found | installed |

## 自動修正

不整合が見つかった場合、ユーザーに確認の上で:
- `version:` を実際の値に更新
- `status:` を `outdated` / `broken` / `inactive` に変更
- `updated:` を今日の日付に更新
