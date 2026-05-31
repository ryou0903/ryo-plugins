---
name: monorepo-install
description: "ryo-pluginsモノレポに新しいプラグインをインストールする。「プラグイン追加して」「モノレポにインストール」「ryo-pluginsに登録」「monorepo-install」「新しいplugin作って登録まで」のような指示で発動する。"
allowed-tools: Bash, Read, Edit, Write, AskUserQuestion
---

# monorepo-install

ryo-plugins モノレポに新しい Claude Code プラグインを作成・登録する。
ファイル配置だけでは認識されない。**3箇所の登録が全て必要**。

## パス定数

```
MARKETPLACE = ~/.claude/plugins/marketplaces/ryo-plugins
CACHE       = ~/.claude/plugins/cache/ryo-plugins
INSTALLED   = ~/.claude/plugins/installed_plugins.json
```

## 手順

### Step 1: 情報収集

ユーザーに以下を確認（AskUserQuestion を使う）:

- **プラグイン名**: kebab-case（例: `hermes-x`）
- **説明**: 1行の英語概要
- **カテゴリ**: `productivity` / `development` / `creative`
- **バージョン**: デフォルト `0.1.0`
- **含めるコンポーネント**: skills / agents / hooks / commands（複数可）

### Step 2: ファイル作成

マーケットプレース側にディレクトリとファイルを作る:

```
{MARKETPLACE}/plugins/{name}/
  .claude-plugin/plugin.json
  skills/{skill-name}/SKILL.md      ← スキルがある場合
  agents/{agent-name}/AGENT.md      ← エージェントがある場合
  hooks/{hook-file}.md              ← フックがある場合
  commands/{command-name}/COMMAND.md ← コマンドがある場合
```

**plugin.json テンプレート:**

```json
{
  "name": "{name}",
  "version": "{version}",
  "description": "{description}",
  "author": { "name": "ryou0903" },
  "license": "MIT"
}
```

### Step 3: marketplace.json に登録 (これを忘れると認識されない)

`{MARKETPLACE}/.claude-plugin/marketplace.json` の `plugins` 配列末尾に追加:

```json
{
  "name": "{name}",
  "description": "{description}",
  "source": "./plugins/{name}",
  "category": "{category}"
}
```

**Edit ツールで既存の最後のエントリの閉じ `}` の後に追加する。**

### Step 4: installed_plugins.json に登録

`{INSTALLED}` に以下のエントリを追加:

```json
"{name}@ryo-plugins": [
  {
    "scope": "user",
    "installPath": "{CACHE}/{name}/{version}",
    "version": "{version}",
    "installedAt": "{ISO8601_NOW}",
    "lastUpdated": "{ISO8601_NOW}"
  }
]
```

**Edit ツールで最後のプラグインエントリの `]` の後にカンマ + 新エントリを追加する。**

### Step 5: キャッシュにコピー

```bash
mkdir -p {CACHE}/{name}/{version}
cp -r {MARKETPLACE}/plugins/{name}/.claude-plugin {CACHE}/{name}/{version}/
cp -r {MARKETPLACE}/plugins/{name}/skills {CACHE}/{name}/{version}/ 2>/dev/null
cp -r {MARKETPLACE}/plugins/{name}/agents {CACHE}/{name}/{version}/ 2>/dev/null
cp -r {MARKETPLACE}/plugins/{name}/hooks {CACHE}/{name}/{version}/ 2>/dev/null
cp -r {MARKETPLACE}/plugins/{name}/commands {CACHE}/{name}/{version}/ 2>/dev/null
cp -r {MARKETPLACE}/plugins/{name}/reference {CACHE}/{name}/{version}/ 2>/dev/null
```

### Step 6: 完了報告

以下をユーザーに伝える:

1. 登録完了した旨
2. **`/reload-plugins` を実行して反映してください**
3. 新セッションでも使えるようになる旨

## よくあるミス（実体験）

| ミス | 症状 | 対処 |
|------|------|------|
| marketplace.json 未登録 | `/reload-plugins` してもスキルリストに出ない | Step 3 を実行 |
| installed_plugins.json 未登録 | プラグイン数が増えない | Step 4 を実行 |
| キャッシュ未コピー | installPath が見つからずエラー | Step 5 を実行 |
| Hermesのスキルと混同 | `~/.hermes/skills/` に置いてしまう | Claude Code は `~/.claude/plugins/` 配下 |

## 検証チェックリスト

全ステップ完了後に確認:

```bash
# 1. マーケットプレースにディレクトリがあるか
ls {MARKETPLACE}/plugins/{name}/.claude-plugin/plugin.json

# 2. marketplace.json に登録されているか
grep '"name": "{name}"' {MARKETPLACE}/.claude-plugin/marketplace.json

# 3. installed_plugins.json に登録されているか
grep '{name}@ryo-plugins' {INSTALLED}

# 4. キャッシュにコピーされているか
ls {CACHE}/{name}/{version}/.claude-plugin/plugin.json
```

全て OK なら `/reload-plugins` で反映される。
