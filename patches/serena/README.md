# serena patches

`serena-agent`（oraios/serena, MCP + Claude Code hooks）に対するカスタム拡張の恒久バックアップ。

serena の hook は `~/.claude/settings.json` から `serena-hooks` CLI を呼ぶが、**ディレクトリ別に無効化する機能が serena 本体に存在しない**（`SessionStartActivateProjectHook` は cwd も env も見ずに「Activate the project... Follow this instruction before doing anything else」をハードコードで毎回注入する）。

そこで `serena-hooks` を直接呼ばず、**前段にゲート用ラッパーを挟む**。serena 本体（`~/.local/share/uv/tools/serena-agent/`）は一切 patch しないので、**serena アップデートで壊れない**。settings.json を元に戻すだけで完全に無効化できる。

> 公開リポジトリのため、**実ディレクトリパスは置かない**。無効化リストの実体はローカル限定（`~/.serena/disabled_dirs.txt`）。ここにはテンプレ（`.example`）のみ。

## ファイル

| File | 役割 |
|---|---|
| `serena-hooks-gated` | ゲート用ラッパー。hook の stdin から cwd を読み、無効化リストに該当すれば**入力を飲み込んで黙って終了**（注入・ナッジ・自動承認・cleanup を全停止）。非該当なら本物の `serena-hooks` に素通し |
| `disabled_dirs.example.txt` | 無効化ディレクトリリストのテンプレ |

## 仕組み（serena-hooks-gated）

1. hook payload の `.cwd`（無ければ `$PWD`）を取得
2. `~/.serena/disabled_dirs.txt` の各行と**プレフィックス一致**で照合（そのディレクトリ自身 or 配下なら該当）。`/foo` は `/foo-bar` に誤爆しない（境界判定済み）
3. 該当 → `exit 0` で無出力（serena実質オフ）／ 非該当 → `printf '%s' "$INPUT" | serena-hooks "$@"` で素通し

環境変数で差し替え可:
- `SERENA_HOOKS_BIN`（既定 `$HOME/.local/bin/serena-hooks`）
- `SERENA_DISABLED_DIRS_FILE`（既定 `$HOME/.serena/disabled_dirs.txt`）

settings.json 側は4つの hook command を `serena-hooks <cmd>` → `~/.local/bin/serena-hooks-gated <cmd>` に置換する（`activate` / `remind` / `auto-approve` / `cleanup`）。

## 復旧手順（全部忘れた場合）

```bash
# 1. このリポジトリの patches/serena/ を参照
#    https://github.com/ryou0903/ryo-plugins → patches/serena/

# 2. ラッパーを ~/.local/bin/ に戻す
cp patches/serena/serena-hooks-gated ~/.local/bin/serena-hooks-gated
chmod +x ~/.local/bin/serena-hooks-gated

# 3. 無効化リストを用意（実パスはここで手書き、公開リポには入れない）
cp patches/serena/disabled_dirs.example.txt ~/.serena/disabled_dirs.txt
#    → 無効化したい絶対パスを1行ずつ記入

# 4. ~/.claude/settings.json の serena hook 4箇所を差し替え
#    "serena-hooks activate --client=claude-code"
#      → "/Users/<you>/.local/bin/serena-hooks-gated activate --client=claude-code"
#    同様に remind / auto-approve / cleanup も
```

反映は次回そのディレクトリでセッション起動したときから（フックは毎回リストを読み直す）。
