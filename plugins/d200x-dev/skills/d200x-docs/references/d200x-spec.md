# Ulanzi D200X Stream Controller (Creative Deck)

Model: A045 (D200X)
前モデル: D200 (A015)


## ハードウェア仕様

ディスプレイ: 5.5インチ LCD, 960x540 RGB, 各キーに個別ミニディスプレイ搭載

操作系:
- LCDキー: 13個（カスタマイズ可能、各196x196 px）
- ロータリーエンコーダ: 3個（回転 + 押し込みクリック対応）
- エンコーダフィードバック表示: ボタングリッド右下の横長エリア（458x196 px、3分割で各126x140 px）
  エンコーダ未割当時はSmall Windowモード（時計/CPU・MEM・GPU使用率）にフォールバック
- ページ切替ボタン: 2個（物理ボタン）
- マルチページ対応により割当可能アクション数は42以上

キーレイアウト:
```
Row 0:  [ 0] [ 1] [ 2] [ 3] [ 4]
Row 1:  [ 5] [ 6] [ 7] [ 8] [ 9]
Row 2:  [10] [11] [12] [=Encoder=]
```
- キー0〜12: 標準Keypadキー（196x196 px）、プラグインSDKで自由にカスタマイズ可能
- 右下横長エリア: エンコーダフィードバック表示（3ダイアル分）。プラグインSDKのEncoder layoutで制御
- グリッドアドレス: "{col}_{row}" 形式（col = index % 5, row = index // 5）

本体:
- 寸法: 153 x 113.5 x 98 mm
- 本体重量: 約480g / 梱包重量: 約720g
- 素材: ABS + PC筐体、アルミ合金フェイスプレート、アクリルキー
- 底面: 滑り止めシリコンパッド
- 角度調整: 不可（固定）
- 付属ケーブル: USB-C 編み込み 1m

接続ポート（8-in-1 統合ドック）:
- USB-C (ホスト): USB 3.2 Gen 2 (10Gbps) — PC接続用
- USB-A (ホスト): USB 3.2 Gen 2 (10Gbps)
- USB-C (データ/充電出力): USB 3.2 Gen 2, PD 3.0, 最大85W出力
- USB-C (電源入力): PD 3.0, 最大100W入力
- HDMI: 4K@60Hz (4096x2160), HDCP 1.4/2.2
- SDカードスロット: SD 3.0
- TF/microSDスロット: TF 3.0
- 3.5mmオーディオ: ヘッドホン出力 + マイク入力（デュアル機能）

電源:
- 消費電力: 最大10W (5V/2A)
- PD入力: 最大100W（ラップトップへのパススルー充電用）

無線:
- D200X本体: USB-C有線接続のみ（Bluetooth/WiFiなし）
- 別売Ulanzi Dial: Bluetooth対応（最大3台接続）


## ソフトウェア

Ulanzi Studio 3.0:
- ダウンロード: https://www.ulanzi.com/pages/ulanzi-app
- 対応OS: Windows 10以降 / macOS Monterey 12.0以降
- 料金: 完全無料（サブスクリプションなし）
- 対応言語: zh_CN, zh_HK, en, ja_JP, de_DE, ko_KR, pt_PT, es_ES

動作モード:
- オンラインモード: Ulanzi Studio経由でフルカスタマイズ
- オフラインモード: 保存済みプロファイルでプラグアンドプレイ

プロファイル:
- マルチプロファイル・マルチページ対応
- プロファイル内に最大10フォルダ
- フォアグラウンドアプリ検出による自動プロファイル切替
- バッチインポート/エクスポート対応


## プラグインSDK & API

リポジトリ:
- GitHub: https://github.com/UlanziTechnology
- UlanziDeckPlugin-SDK — メインSDKドキュメント・サンプル (AGPL-3.0)
- plugin-common-node — Node.js SDKライブラリ
- plugin-common-html — HTML/WebView SDKライブラリ

プロトコル:
- Ulanzi JS Plugin Development Protocol v2.1.2
- WebSocket通信: 127.0.0.1:3906
- 設定ファイル形式: JSON

プラグインタイプ:
- HTML: WebViewランタイム、設定UIはHTML (Property Inspector)
- Node.js: サーバーサイドランタイム、設定UIはHTML (Property Inspector)

プラグインディレクトリ構造:
```
com.ulanzi.{pluginName}.ulanziPlugin/
  manifest.json
  libs/
  resources/
  plugin/
    app.js (or app.html)
  property-inspector/
    inspector.html
```

manifest.json 構造:
```json
{
  "Author": "作者名",
  "Name": "プラグイン名",
  "Description": "説明",
  "Icon": "resources/icon.png",
  "Version": "1.0.0",
  "UUID": "com.ulanzi.ulanzistudio.{pluginName}",
  "Type": "JavaScript",
  "CodePath": "plugin/app.js",
  "Actions": [{
    "Name": "アクション名",
    "Icon": "resources/action-icon.png",
    "UUID": "com.ulanzi.ulanzistudio.{pluginName}.{action}",
    "PropertyInspectorPath": "property-inspector/inspector.html",
    "Controllers": ["Keypad"],
    "Devices": [],
    "States": [{"Name": "Default", "Image": "..."}],
    "Encoder": {"layout": "$UA1"}
  }],
  "OS": [
    {"Platform": "windows", "MinimumVersion": "10"},
    {"Platform": "mac", "MinimumVersion": "10.11"}
  ]
}
```

UUID命名規則:
- プラグインUUID: 4セグメント（例: com.ulanzi.ulanzistudio.myplugin）
- アクションUUID: 5セグメント以上（例: com.ulanzi.ulanzistudio.myplugin.toggle）

コントローラータイプ:
- Keypad: 13個のLCDキー（各196x196 px）
- Encoder: 3個のロータリーダイアル。右下横長エリアにフィードバック表示（全体458x196 px、各スロット126x140 px）。レイアウト $UA1 / $UA2 / カスタム layout.json

主要APIイベント:
- キー: onAdd, onRun, onKeyDown, onKeyUp, onSetActive, onClear
- エンコーダ: onDialDown, onDialUp, onDialRotate
- 通信: onSendToPlugin, onSendToPropertyInspector

主要APIメソッド:
- アイコン: setStateIcon(), setPathIcon(), setBaseDataIcon(), setGifPathIcon(), setGifDataIcon()
- 設定: setSettings(), getSettings(), setGlobalSettings(), getGlobalSettings()
- システム: toast(), hotkey(), openUrl(), openView(), selectFileDialog(), selectFolderDialog(), logMessage(), showAlert()

デバッグ（Ulanzi Studio起動オプション）:
- --log: ログ有効化
- --logLevel: ログレベル指定
- --webRemoteDebug: WebViewリモートデバッグ（ポート9292）
- --nodeRemoteDebug: Node.jsリモートデバッグ

SDK対応デバイス: D200, D200H, Dial, D200X


## 対応アプリケーション（100以上）

- 配信: OBS, Streamlabs, Twitch, YouTube
- 映像編集: Premiere Pro, Final Cut Pro, DaVinci Resolve, CapCut
- 画像編集: Photoshop, Lightroom
- 通信: Zoom, Microsoft Teams, Discord
- スマートホーム: Philips Hue, Home Assistant, Govee, Nanoleaf, Yeelight

プラグインマーケットプレイス: https://ugc.ulanzistudio.com/


## 競合比較

D200X vs Elgato Stream Deck+:
- LCDキー: D200X 13個 / Elgato 8個
- ダイアル: D200X 3個 / Elgato 4個
- タッチストリップ: D200X なし / Elgato あり
- 統合ハブ: D200X 8-in-1 / Elgato なし
- HDMI: D200X 4K@60Hz / Elgato なし
- カードリーダー: D200X SD+TF / Elgato なし
- USB PD: D200X 100W入/85W出 / Elgato なし
- 接続: 両方USB-C有線
- SDK: D200X AGPL-3.0公開 / Elgato 成熟したエコシステム
- 価格: D200X $96-130 / Elgato ~$200

D200X vs Logitech MX Creative Console:
- LCDキー: D200X 13個 / Logitech 9個
- ダイアル: D200X 3個 / Logitech 2個（ホイール+ローラー）
- 統合ハブ: D200X 8-in-1 / Logitech なし
- 接続: D200X USB-C有線 / Logitech Bluetooth無線
- 価格: D200X $96-130 / Logitech ~$200

D200Xの強み:
- 8-in-1統合ドック — カテゴリ内で唯一。USBハブ・HDMI・カードリーダーを内蔵
- 低価格 — 競合の約半額
- サブスクなし — ソフトウェア・プラグイン・アップデートすべて無料
- オープンSDK — AGPL-3.0でGitHub公開、WebSocketプロトコル完全文書化

D200Xの弱点:
- プラグインエコシステムがElgatoより小規模
- 角度調整不可
- ボタン押し込みがやや硬い（D200レビューより、D200Xで改善の可能性あり）
- ソフトウェアの成熟度がElgatoに劣る
- タッチストリップなし

価格:
- USD: $96-130
- JPY: 17,999円（税込）


## 参考リンク

- 公式製品ページ: https://www.ulanzi.com/products/d200x-creative-deck
- Ulanzi Japan: https://www.ulanzi.jp/products/ulanzi-d200x-creative-deck-a045
- SDK (GitHub): https://github.com/UlanziTechnology/UlanziDeckPlugin-SDK
- plugin-common-node: https://github.com/UlanziTechnology/plugin-common-node
- plugin-common-html: https://github.com/UlanziTechnology/plugin-common-html
- HA Hub for UlanziDeck: https://github.com/weemaba999/ha-hub-ulanzi
