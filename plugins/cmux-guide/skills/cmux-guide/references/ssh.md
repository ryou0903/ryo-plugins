# cmux SSH

`cmux ssh` でリモートマシン用のワークスペースを作成。

## 基本コマンド

```bash
cmux ssh user@remote
cmux ssh user@remote --name "dev server"
cmux ssh user@remote -p 2222
cmux ssh user@remote -i ~/.ssh/id_ed25519
```

`~/.ssh/config` のホストエイリアス、アイデンティティファイル、プロキシ設定を読み込む。

## フラグ

- `--name` — ワークスペースタイトル
- `-p, --port` — SSHポート（デフォルト22）
- `-i, --identity` — アイデンティティファイル
- `-o, --ssh-option` — 任意のSSHオプション
- `--no-focus` — フォーカスなしで作成

## 主な機能

### ブラウザペーン
SSHワークスペース内のブラウザペーンはリモートネットワーク経由でHTTP/WebSocketトラフィックをルーティング。`localhost:3000` でリモートサーバーのサービスにアクセス可能。

### ドラッグ&ドロップ
ファイル/画像をドラッグすると scp でアップロード。ControlMaster多重化を活用。

### 通知
リモートプロセスがローカルの cmux コマンドを呼び出し可能。per-host cooldownでスパム抑制。

### リモートエージェント
`cmux claude-teams` と `cmux omo` がSSHセッション内で動作。

## 再接続

接続切断時に指数バックオフで再接続:
- 3秒 → 6秒 → 12秒 → ... → 最大60秒
- リモートセッションは永続化、再接続時に復帰
- keepaliveオプション自動注入

## リレーデーモン（cmuxd-remote）

初回接続時にリモートホストをプローブ（uname検証）し `cmuxd-remote` バイナリをアップロード。

処理内容:
- SOCKS5/HTTP CONNECTでブラウザトラフィック代理
- HMAC-SHA256認証付きリバースTCPトンネル
- セッション永続化とPTYリサイズ管理

バイナリはSHA-256マニフェスト検証済み。
