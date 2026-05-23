# D200X ドキュメントリファレンス

Ulanzi D200X Stream Controllerのプラグイン開発に必要な仕様・SDK・環境情報を参照するスキル。「D200Xの仕様」「プラグインの作り方」「SDKのAPI」「マニフェストの書き方」「エンコーダーレイアウト」「インストールパス」「デバッグ方法」「キーサイズ」「WebSocket」のような質問で発動する。

## 対応トピック

ユーザーの質問に応じて、以下のリファレンスを参照して回答する:

- ハードウェア仕様・キーレイアウト・画像サイズ・エンコーダー → `references/d200x-spec.md`
- SDK API・マニフェスト・WebSocketプロトコル・イベント・送信メソッド → `references/plugin-dev-guide.md`
- macOS環境・インストールパス・ログ・デバッグ手順 → `references/macos-environment.md`

## 回答ルール

1. まずユーザーの質問に最も関連するリファレンスファイルを特定し、その内容を読んで回答する
2. 具体的な数値（ピクセルサイズ、ポート番号、パス）を含めて正確に回答する
3. 日本語で回答する

## クイックリファレンス

### ハードウェア
- キーパッドキー: 13個 (各196x196 px)
- エンコーダーフィードバック: 458x196 px (3スロット x 126x140 px)
- レイアウトグリッド: 5x3 (最後のセルはエンコーダー)

### SDK
- プロトコル: Ulanzi JS Plugin Development Protocol V2.1.2
- WebSocket: 127.0.0.1:3906
- Node.js: v20.18.0 (Ulanzi Studio 3.0.15バンドル)
- プラグインパス: ~/Library/Application Support/Ulanzi/UlanziDeck/Plugins/

### マニフェスト
- UUID: 4セグメント = プラグイン、5+セグメント = アクション
- Hotkey形式 (macOS): Unicode修飾子 (⌘C, ⌥⇧V)
