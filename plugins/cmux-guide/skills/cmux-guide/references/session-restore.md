# cmux セッション復元

## 復元される項目

- ウィンドウ、ワークスペース、ペインのレイアウト
- 作業ディレクトリ
- ターミナルのスクロールバック（ベストエフォート）
- ブラウザURLとナビゲーション履歴

**復元されない:** ライブプロセス状態（tmux, vim, シェルなど）

## エージェントセッション復元

```bash
cmux hooks setup
cmux hooks setup [エージェント名]
```

Claude Code, Codex, Grok などの対応エージェントセッションを自動復元。

## カスタム復元コマンド

```bash
cmux surface resume set --kind tmux --checkpoint work --shell "コマンド"
cmux surface resume show --json
cmux surface resume clear --checkpoint work
```

承認済みプレフィックスは **設定 > ターミナル > 復元コマンド** で管理。

## 仕組み

1. JSONスナップショットを `~/Library/Application Support/cmux/session-` に保存
2. スクロールバックは一時ファイル経由で再生
3. エージェントフックが `~/.cmuxterm/` にセッション情報を記録
4. 復元時、ウィンドウ再構築後にエージェント復元コマンド実行

## 自動復元の無効化

設定画面で「再オープン時にエージェントセッションを復元」をオフ、または:

```json
{"terminal": {"autoResumeAgentSessions": false}}
```

レイアウト、作業ディレクトリ、スクロールバック、ブラウザ履歴は引き続き復元される。
