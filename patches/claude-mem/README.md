# claude-mem patches

`thedotmack/claude-mem` プラグインに対するカスタムパッチの恒久バックアップ。

claude-mem のパッチは `~/.claude/plugins/cache/thedotmack/claude-mem/<version>/scripts/` 内のファイルを書き換えるため、**プラグイン更新で消える**。さらに `npx claude-mem uninstall` は `~/.claude-mem/` ごと削除しうる。そのため、ここ（git + GitHub）にスクリプト本体を置いて恒久化する。

> 公開リポジトリのため、**秘密情報・実ディレクトリパスは置かない**。`disabled-dirs.json` の実体はローカル限定（`~/.claude-mem/disabled-dirs.json`）。ここにはテンプレ（`.example`）のみ。

## ファイル

| File | 役割 |
|---|---|
| `patch-disabled-dirs.py` | **ディレクトリ別無効化**。`~/.claude-mem/disabled-dirs.json` に書いたディレクトリ＆配下で、コンテキスト注入もログ取りも停止 |
| `disabled-dirs.example.json` | 上記の除外リストのテンプレ |
| `patch-codex-worker.py` | Codexプロバイダー用ワーカーパッチ（旧バージョン系） |
| `patch-codex-worker-13.3.py` | Codexプロバイダー用ワーカーパッチ（13.3系） |
| `patch-codex.sh` | ワーカー+UI 統合パッチ（Codex） |
| `patch-openai.sh` | OpenAI系パッチ |

## ディレクトリ別無効化の仕組み（patch-disabled-dirs.py）

`worker-service.cjs`（minified bundle）に対して冪等に:

1. ヘルパー `__cmDisabledDirs()` / `__cmIsDisabledDir(cwd)` を挿入（`disabled-dirs.json` を読み、cwd が「リスト内ディレクトリ or その配下」かをプレフィックス一致で判定）
2. **ログ系の関門** `Um(t)` に `if(__cmIsDisabledDir(t))return!1;` を追加 → observation / file-context / session-init / summarize 全停止
3. **SessionStart 注入** `TX.execute` 冒頭にガード追加 → 起動時の "recent context" 注入を停止

`/secret` は `/secretXYZ` に誤爆しない（境界判定済み）。built-in の `CLAUDE_MEM_EXCLUDED_PROJECTS` はログ系のみ除外し SessionStart 注入を塞げないため、本パッチで補完している。

## 復旧手順（全部忘れた場合）

```bash
# 1. このリポジトリを clone（既にあればそのパスを使う）
#    https://github.com/ryou0903/ryo-plugins → patches/claude-mem/

# 2. スクリプトを ~/.claude-mem/ に戻す
mkdir -p ~/.claude-mem
cp patches/claude-mem/patch-*.py patches/claude-mem/patch-*.sh ~/.claude-mem/

# 3. 除外リストを用意（実パスはここで手書き、公開リポには入れない）
cp patches/claude-mem/disabled-dirs.example.json ~/.claude-mem/disabled-dirs.json
#    → disabled 配列に実ディレクトリのフルパスを記入

# 4. パッチ適用（冪等。プラグイン更新後も同じコマンドで再適用）
python3 ~/.claude-mem/patch-disabled-dirs.py

# Codex系も必要なら
bash ~/.claude-mem/patch-codex.sh
```

反映は次回そのディレクトリでセッション起動したときから（フックは毎回ファイルを読み直すのでワーカー再起動不要）。
