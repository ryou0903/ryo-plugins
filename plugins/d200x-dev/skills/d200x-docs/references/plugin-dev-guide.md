# Ulanzi D200X プラグイン開発ガイド

プロトコルバージョン: Ulanzi JS Plugin Development Protocol V2.1.2
対応ホスト: Ulanzi Studio 3.0.11以降
Node.jsランタイム: v20.18.0（Ulanzi Studio 3.0.15バンドル。SDKドキュメントはv20.12.2と記載）
ライセンス: AGPL-3.0 (SDK)


## SDKリポジトリ

- UlanziDeckPlugin-SDK: https://github.com/UlanziTechnology/UlanziDeckPlugin-SDK
  メインドキュメント・デモプラグイン・シミュレータ
- plugin-common-node: https://github.com/UlanziTechnology/plugin-common-node
  Node.js SDKライブラリ (npm: ulanzideck-api v0.1.0, 依存: ws@^8.18.0, ESM)
- plugin-common-html: https://github.com/UlanziTechnology/plugin-common-html
  HTML/WebView SDKライブラリ（ブラウザ用、npmパッケージなし）


## プラグイン作成手順

1. フォルダ構造を作成（命名規則: com.ulanzi.{pluginName}.ulanziPlugin）
2. メインサービスのタイプを選択（HTMLまたはNode.js）
3. SDKライブラリをコピー
   - HTML: plugin-common-html の内容を libs/ へ
   - Node.js: plugin-common-node の ulanzi-api/ をプラグインディレクトリへ、npm install ws
4. manifest.json を設定（必須フィールド: Author, Name, Icon, Version, CodePath, Type, UUID, Actions）
5. メインサービスを実装（$UD.connect → イベントハンドラ登録）
6. Property Inspector を実装（任意）
7. ローカライズファイルを追加（任意）
8. シミュレータでテスト
9. デスクトップアプリでテスト


## ディレクトリ構造

```
com.ulanzi.{pluginName}.ulanziPlugin/
  manifest.json
  libs/
  resources/
  plugin/
    app.html (HTMLプラグイン) or app.js (Node.jsプラグイン)
  property-inspector/
    inspector.html
  en.json
  zh_CN.json
  zh_HK.json
  ja_JP.json
  de_DE.json
  ko_KR.json
  pt_PT.json
  es_ES.json
```


## UUID命名規則

- プラグインUUID: 正確に4セグメント（例: com.ulanzi.ulanzistudio.myplugin）
- アクションUUID: 5セグメント以上（例: com.ulanzi.ulanzistudio.myplugin.toggle）
- SDKはセグメント数でメインサービスとアクションを判別する（4=メインサービス、4超=アクション）


## manifest.json 完全リファレンス

トップレベルフィールド:
- Author (string, 必須): 開発者名
- Name (string, 必須): プラグイン名。ホストアプリのプラグインリストに表示
- Description (string, 任意): プラグイン説明
- Icon (string, 必須): プラグインアイコンパス。SVG/PNG/JPG対応
- Version (string, 必須): バージョン番号
- Category (string, 任意): プラグインカテゴリ名
- CategoryIcon (string, 任意): カテゴリアイコンパス
- CodePath (string, 必須): メインエントリポイント。.html→QWebEngineViewで読込、.js→Node.jsで読込
- Type (string, 必須): 固定値 "JavaScript"
- Inspect (string, 任意): Node.jsリモートデバッグアドレス（例: "--inspect=127.0.0.1:9201"）。プラグインごとにユニークなポートが必要。--nodeRemoteDebugフラグ必須
- PrivateAPI (boolean, 任意): プライベートAPI使用有無
- UUID (string, 必須): プラグイン一意識別子。4セグメント形式
- Actions (array, 必須): アクション定義リスト
- OS (array, 任意): 対応OS・最低バージョン
- Software (object, 任意): ホストアプリバージョン要件。Software.MinVersion で指定（MinimumVersionは非推奨）
- ApplicationsToMonitor (object, 任意): 監視対象アプリ。起動/終了イベントをプラグインに通知
- Profiles (array, 任意): プロファイル設定
- InstallToDepsApp (object, 任意): サードパーティアプリと並行して実行するスクリプト
  - Type (string): 固定値 "JavaScript"
  - CodePath (string): 実行スクリプトパス（プラグインルートからの相対）

Actionフィールド:
- Name (string, 必須): アクション名
- Icon (string, 必須): アクションアイコン（プラグインリスト表示用）
- PropertyInspectorPath (string, 任意): Property Inspector HTMLファイルパス（プラグインルートからの相対パス）
- state (number, 任意): デフォルトアクティブステートインデックス。デフォルト0
- States (array, 必須): アイコンステートリスト。各要素は Name (string) と Image (string, アイコンパス)
- Tooltip (string, 任意): ツールチップ
- UUID (string, 必須): アクション一意識別子。5セグメント以上
- SupportedInMultiActions (boolean, 任意): マルチアクション対応。デフォルトtrue
- DisableAutomaticStates (boolean, 任意): 自動ステート切替を無効化。デフォルトfalse
- Controllers (array, 任意): 対応コントローラータイプ "Keypad" / "Encoder"。デフォルトはKeypadのみ
- Devices (array, 任意): 対応デバイスモデル。空配列=全デバイス
- Encoder (object, 任意): ダイアルレイアウト設定。ControllersにEncoderを含む場合のみ有効

Devicesフィールド構文:
- []: 全デバイス（推奨デフォルト）
- ["D200X"]: D200Xのみ
- ["~Dial"]: Dial以外の全デバイス
- ["D200", "~Dial"]: D200を含み、Dialを除外
- 対応デバイスモデル: D200, D200H, Dial, D200X

ApplicationsToMonitor例:
```json
{
  "windows": ["obs32.exe", "obs64.exe"],
  "mac": ["com.obsproject.obs-studio"]
}
```

Profilesフィールド:
- Name (string): プロファイル名
- DeviceType (number): 対象デバイスタイプ
- Readonly (boolean): 読み取り専用
- DontAutoSwitchWhenInstalled (boolean): インストール後の自動切替を防止
- AutoInstall (boolean): 自動インストール

manifest.json完全例:
```json
{
  "Author": "Ulanzi",
  "Name": "OBS Studio",
  "Description": "OBS Studio Operation",
  "Icon": "resources/store_icon.png",
  "Version": "1.0.1",
  "Category": "OBS Studio",
  "CategoryIcon": "resources/icon.png",
  "CodePath": "source/main.html",
  "Type": "JavaScript",
  "Inspect": "--inspect=127.0.0.1:9201",
  "PrivateAPI": true,
  "UUID": "com.ulanzi.ulanzistudio.obsstudio",
  "Actions": [
    {
      "Name": "Record",
      "Icon": "resources/actions/record/icon.png",
      "PropertyInspectorPath": "source/actions/record/inspector.html",
      "state": 0,
      "States": [
        { "Name": "Start", "Image": "resources/actions/record/on.png" },
        { "Name": "Stop",  "Image": "resources/actions/record/off.png" }
      ],
      "Tooltip": "Start/Stop recording to file",
      "UUID": "com.ulanzi.ulanzistudio.obsstudio.record",
      "SupportedInMultiActions": false,
      "DisableAutomaticStates": true,
      "Controllers": ["Keypad"],
      "Devices": [],
      "Encoder": {
        "layout": "$UA1"
      }
    }
  ],
  "OS": [
    { "Platform": "windows", "MinimumVersion": "10" },
    { "Platform": "mac", "MinimumVersion": "10.11" }
  ],
  "Software": {
    "MinVersion": "2.1.0"
  },
  "ApplicationsToMonitor": {
    "windows": ["obs32.exe", "obs64.exe"],
    "mac": ["com.obsproject.obs-studio"]
  }
}
```


## アイコン・画像仕様

D200Xキーレイアウト:
```
Row 0:  [ 0] [ 1] [ 2] [ 3] [ 4]
Row 1:  [ 5] [ 6] [ 7] [ 8] [ 9]
Row 2:  [10] [11] [12] [=Encoder=]
```
- キー0〜12: 標準Keypadキー（13個）。各196x196 px。プラグインSDKで自由にカスタマイズ可能
- 右下横長エリア: エンコーダフィードバック表示（3ダイアル分）。プラグインSDKのEncoder layoutで制御
  エンコーダ未割当時はSmall Windowモード（時計/CPU・MEM・GPU使用率）にフォールバック
- グリッドアドレス: "{col}_{row}" 形式（col = index % 5, row = index // 5）

Keypadアイコン標準サイズ: 196 x 196 px
（HTML SDKの Utils.drawImage() / Utils.drawText() のデフォルトキャンバスサイズ）

エンコーダフィードバック表示（右下横長エリア）:
- 全表示エリア: 458 x 196 px
- 各ダイアルスロット: 126 x 140 px（3分割）
- ホスト側スケールファクタ: 0.286
- デバイス側スケールファクタ: 0.75
- 原点: (0, 0) 左上、(126, 140) 右下

対応画像フォーマット:
- 静的アイコン: PNG, JPG, SVG
- アニメーション: GIF（setGifDataIcon / setGifPathIcon 経由）
- 動的アイコン: Base64エンコードされたPNG/JPG/SVG（setBaseDataIcon経由）
- Canvas描画: Utils.drawText() / Utils.drawImage() がデフォルト196x196のbase64 PNGを生成

アイコンタイプコード（WebSocketプロトコルのstateコマンド）:
- type 0: manifestのStatesインデックス参照。dataフィールド: state（インデックス番号）
- type 1: Base64カスタム画像。dataフィールド: data（base64文字列）
- type 2: ローカルファイルパス。dataフィールド: path（プラグインルートからの相対パス）
- type 3: Base64 GIF。dataフィールド: gifdata（base64文字列）
- type 4: ローカルGIFファイルパス。dataフィールド: gifpath（プラグインルートからの相対パス）

各stateメッセージは以下も含む:
- textData: オーバーレイテキスト（なければ空文字列）
- showtext: テキスト表示有無（boolean）


## エンコーダレイアウトシステム

レイアウト設定方法:

manifest.jsonで指定:
```json
"Encoder": {
  "layout": "$UA1"
}
```
ビルトインレイアウト（$UA1, $UA2）またはカスタム layout.json（manifest.jsonと同ディレクトリ）を指定。

動的変更: setFeedbackLayout（manifest.mdで言及されているが、plugin-common-node / plugin-common-html 両SDKのソースコードに未実装。2026-05時点）

ビルトインレイアウト $UA1（アイコン + テキスト）:
```json
{
  "id": "$UA1",
  "items": [
    {
      "type": "pixmap",
      "key": "icon",
      "background": "transparent",
      "enabled": true,
      "rect": [13, 0, 100, 100],
      "zOrder": 0,
      "value": "images/hotkey.svg"
    },
    {
      "type": "text",
      "key": "title",
      "background": "transparent",
      "enabled": true,
      "rect": [0, 105, 126, 35],
      "zOrder": 1,
      "alignment": "center",
      "color": "#dfdfdf",
      "font": { "size": 7 },
      "text": ""
    }
  ]
}
```

ビルトインレイアウト $UA2（テキスト + テキスト）:
```json
{
  "id": "$UA2",
  "items": [
    {
      "type": "text",
      "key": "text2",
      "background": "#000000",
      "enabled": true,
      "opacity": 1,
      "rect": [28, 7, 126, 70],
      "zOrder": 0,
      "alignment": "center",
      "color": "white",
      "font": { "size": 8 },
      "text": "test1"
    },
    {
      "type": "text",
      "key": "title",
      "background": "#000000",
      "enabled": true,
      "rect": [0, 95, 126, 39],
      "zOrder": 1,
      "alignment": "center",
      "color": "white",
      "font": { "size": 8 },
      "text": "test"
    }
  ]
}
```

特殊キー名:
- "icon": ボタンの標準アイコンとして動作
- "title": ボタンの標準タイトルとして動作（ホストアプリのユーザー設定を継承）
- その他のキー名: プロトコルコール経由で手動更新が必要

テキスト要素プロパティ (type: "text"):
- type (string, 必須): "text"
- key (string, 必須): レイアウト内でユニーク
- background (string, 任意): 色、hex、またはグラデーション（"0:#ff0000,1:#00ff00"）
- enabled (boolean, 任意): falseで非表示。デフォルトtrue
- opacity (number, 任意): 0.1〜1、ステップ0.1。デフォルト1
- rect (array/object, 必須): [x, y, width, height] または {x, y, width, height}
- zOrder (number, 任意): 0-700。値が大きいほど前面に描画。デフォルト0
- alignment (string, 任意): "center" / "left" / "right"。デフォルト"center"
- color (string, 任意): テキスト色。デフォルト"white"
- font (object, 任意): { "size": number, "weight": number }
- text (string, 必須): 表示テキスト
- textOverflow (string, 任意): "ellipsis" で省略記号付き切り詰め

画像要素プロパティ (type: "pixmap"):
- type (string, 必須): "pixmap"
- key (string, 必須): レイアウト内でユニーク
- background (string, 任意): 色またはグラデーション
- enabled (boolean, 任意): falseで非表示。デフォルトtrue
- opacity (number, 任意): 0.1〜1。デフォルト1
- rect (array/object, 必須): 位置とサイズ
- zOrder (number, 任意): 0-700。デフォルト0
- value (string, 必須): ローカルパス（プラグインルートからの相対）または data:image/png;base64,...


## WebSocketプロトコル

接続フロー（Node.js メインサービス）:
1. ホストがCodePathを起動。引数: process.argv[2]=アドレス(デフォルト127.0.0.1), process.argv[3]=ポート(デフォルト3906), process.argv[4]=言語(デフォルトen)
2. プラグインが ws://{address}:{port} へWebSocket接続
3. 接続時にregistrationメッセージを送信:
```json
{
  "code": 0,
  "cmd": "connected",
  "uuid": "com.ulanzi.ulanzistudio.pluginName"
}
```
4. 接続確立。イベントの送受信開始

接続フロー（HTML メインサービス / Property Inspector）:
1. URLクエリパラメータから接続情報を読取: port, address, uuid, key, language, controller, device
2. ホストへWebSocket接続
3. 同じregistrationメッセージを送信
4. controllerパラメータで "Keypad" または "Encoder" を示す（$UD.controller でアクセス可能）

Node.jsプラグインのProperty Inspector接続:
1. Node.jsメインサービスが RandomPort でランダムポート(49152-65535)を生成し、プラグインルートの ws-port.js に書込
2. ws-port.js が window.__port を設定
3. Property InspectorのHTMLが ws-port.js を読込み、そのポートでホストに接続

メッセージ基本構造:
```json
{
  "cmd": "<event_name>",
  "uuid": "<sender_uuid>",
  "key": "<button_key>",
  "actionid": "<action_instance_id>",
  "code": 0
}
```

メインサービスの応答確認: メッセージ受信時にcode:0でエコーバック（SDK自動処理）

Contextパラメータ:
- 形式: uuid + '___' + key + '___' + actionid
- エンコード: $UD.encodeContext(msg) — uuid, key, actionidフィールドを持つオブジェクトから生成
- デコード: $UD.decodeContext(context) — { uuid, key, actionid } を返す
- clearイベントでは、contextがparam配列の各要素に個別にスプライスされる

メッセージフィルタリング: codeプロパティを持ち cmdType !== 'REQUEST' のメッセージは無視される。selectdialog応答は cmdType: 'REQUEST' で通過する


## イベント定数（全29個）

```javascript
Events = {
  CONNECTED: 'connected',
  CLOSE: 'close',
  ERROR: 'error',
  ADD: 'add',
  RUN: 'run',
  PARAMFROMAPP: 'paramfromapp',
  PARAMFROMPLUGIN: 'paramfromplugin',
  SETACTIVE: 'setactive',
  CLEAR: 'clear',
  TOAST: 'toast',
  STATE: 'state',
  OPENURL: 'openurl',
  OPENVIEW: 'openview',
  SELECTDIALOG: 'selectdialog',
  LOGMESSAGE: 'logMessage',
  HOTKEY: 'hotkey',
  SHOWALERT: 'showAlert',
  SENDTOPROPERTYINSPECTOR: 'sendToPropertyInspector',
  SENDTOPLUGIN: 'sendToPlugin',
  GETSETTINGS: 'getSettings',
  SETSETTINGS: 'setSettings',
  DIDRECEIVESETTINGS: 'didReceiveSettings',
  SETGLOBALSETTINGS: 'setGlobalSettings',
  GETGLOBALSETTINGS: 'getGlobalSettings',
  DIDRECEIVEGLOBALSETTINGS: 'didReceiveGlobalSettings',
  KEYDOWN: 'keydown',
  KEYUP: 'keyup',
  DIALEDOWN: 'dialdown',
  DIALEUP: 'dialup',
  DIALROTATE: 'dialrotate'
}
```

注意: SDK定数名 DIALEDOWN / DIALEUP はタイポ（Eが余分）。ワイヤプロトコルでは dialdown / dialup が正しい


## SDK APIリファレンス

受信イベント（ホスト → プラグイン）:

接続:
- $UD.onConnected(fn): WebSocket接続確立
- $UD.onClose(fn): WebSocket切断
- $UD.onError(fn): WebSocketエラー

ボタン/キー:
- $UD.onAdd(message): アクションがキーに割当。message.paramに保存済み設定あり
- $UD.onRun(message): キートリガー（シングルクリック確定後）。メインロジックのエントリポイント
- $UD.onKeyDown(message): キー押下開始（runより先に発火。長押し用）
- $UD.onKeyUp(message): キーリリース
- $UD.onSetActive(message): アクティブ状態変更。message.active = true/false
- $UD.onClear(message): アクション削除。message.paramは配列、各要素に.contextあり

エンコーダ/ダイアル:
- $UD.onDialDown(message): ダイアル押下
- $UD.onDialUp(message): ダイアルリリース
- $UD.onDialRotate(message): 回転。message.rotateEvent = 'left' / 'right' / 'hold-left' / 'hold-right'
- $UD.onDialRotateLeft(message): 左回転（非押下時）
- $UD.onDialRotateRight(message): 右回転（非押下時）
- $UD.onDialRotateHoldLeft(message): 押下中の左回転
- $UD.onDialRotateHoldRight(message): 押下中の右回転

パラメータ/設定:
- $UD.onParamFromApp(message): ホストからアクションページへパラメータ送信
- $UD.onParamFromPlugin(message): プラグインから送信されたパラメータをホストが転送

設定永続化:
- $UD.onDidReceiveSettings(message): getSettings/setSettings後に発火。message.settings
- $UD.onDidReceiveGlobalSettings(message): getGlobalSettings/setGlobalSettings後に発火

クロスページ通信:
- $UD.onSendToPlugin(message): メインサービスがProperty Inspectorからデータ受信
- $UD.onSendToPropertyInspector(message): Property Inspectorがメインサービスからデータ受信

ダイアログ:
- $UD.onSelectdialog(message): ファイル/フォルダダイアログの結果。message.path

送信イベント（プラグイン → ホスト）:

アイコン管理:
- $UD.setStateIcon(context, state, text): manifestのStatesインデックスでアイコン設定
- $UD.setBaseDataIcon(context, base64Data, text): Base64カスタム画像
- $UD.setPathIcon(context, path, text): ローカルファイルパス（プラグインルートからの相対）
- $UD.setGifDataIcon(context, gifdata, text): Base64 GIF
- $UD.setGifPathIcon(context, gifpath, text): ローカルGIFファイルパス

パラメータ:
- $UD.sendParamFromPlugin(settings, context): 設定パラメータ送信（ホストが保存）
- $UD.sendToPropertyInspector(settings, context): メイン→PI パススルー（保存されない）
- $UD.sendToPlugin(settings): PI→メイン パススルー（保存されない）

設定永続化:
- $UD.setSettings(settings, context): アクション固有の設定を保存
- $UD.getSettings(context): アクション設定を要求 → onDidReceiveSettings発火
- $UD.setGlobalSettings(settings, context): プラグイン全体の設定を保存
- $UD.getGlobalSettings(context): グローバル設定を要求 → onDidReceiveGlobalSettings発火

システム関数:
- $UD.toast(msg): トースト通知表示
- $UD.showAlert(context): ボタン上にエラーインジケータ表示
- $UD.logMessage(msg, level): ログファイルに書込（info/debug/warn/error）
- $UD.hotkey(key): OSホットキー発行
- $UD.openUrl(url, local, param): ブラウザでURL開く。クエリパラメータはURL文字列でなくparam引数で渡す
- $UD.openView(url, width, height, x, y, param): ローカルHTMLポップアップを開く
- $UD.selectFileDialog(filter): ファイル選択ダイアログ
- $UD.selectFolderDialog(): フォルダ選択ダイアログ


## Utilsリファレンス

HTML SDK Utils:
- Utils.getFormValue(form): フォームコントロールをオブジェクトとして読取
- Utils.setFormValue(jsn, form): オブジェクトからフォームに値設定
- Utils.debounce(fn, wait): デフォルト150ms
- Utils.drawImage(url, w=196, h=196, canvas, returnCanvas): Promise<base64|canvas>
- Utils.cropImage(url, offsetX, offsetY, w=196, h=196, canvas, returnCanvas)
- Utils.drawText(text, stroke='#fff', bg='#000', wh=196, label, canvas): base64 PNG
- Utils.loadImagePromise(url): Promise<{url, status, img}>
- Utils.htmlFileToBase64(file): FileオブジェクトからBase64データURL
- Utils.getData(url, param): キャッシュバスティング付きGET
- Utils.fetchData(url, param, method, headers): タイムアウト付きFetchラッパー
- Utils.readJson(path): XHR経由でJSON読込
- Utils.getQueryParams(param): URLクエリパラメータ取得
- Utils.getPluginPath(): プラグインルートディレクトリ
- Utils.parseJson(jsonString): 安全なparse。失敗時false
- Utils.getProperty(obj, 'a.b[0].c', default): ディーププロパティアクセス

Node.js SDK Utils:
- Utils.getPluginPath(): プラグインルートディレクトリ（Windows/macOS対応）
- Utils.getSystemType(): 'windows' | 'mac'
- Utils.adaptLanguage(ln): 言語コード正規化
- Utils.parseJson(jsonString): 安全なparse。失敗時false
- Utils.debounce(fn, wait): デフォルト150ms
- Utils.getProperty(obj, dotPath, default): ディーププロパティアクセス
- Utils.log(...msg): タイムスタンプ付きconsole.log
- Utils.warn(...msg): タイムスタンプ付きconsole.warn
- Utils.error(...msg): タイムスタンプ付きconsole.error

RandomPort (Node.jsのみ):
```javascript
import { RandomPort } from './ulanzi-api/index.js';
const rp = new RandomPort(minPort=49152, maxPort=65535);
const port = rp.getPort();  // ポート生成、ws-port.js書出、ポート番号返却
```
生成される ws-port.js の内容: window.__port = <port>;


## Property Inspector

HTMLテンプレート:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="../../libs/css/uspi.css">
</head>
<body>
  <div class="uspi-wrapper">
    <form id="property-inspector">
      <div class="uspi-item">
        <div class="uspi-item-label" data-localize>Name</div>
        <input type="text" class="uspi-item-value" name="name" value="">
      </div>
    </form>
  </div>
  <script src="../../libs/js/constants.js"></script>
  <script src="../../libs/js/eventEmitter.js"></script>
  <script src="../../libs/js/timers.js"></script>
  <script src="../../libs/js/utils.js"></script>
  <script src="../../libs/js/ulanziApi.js"></script>
  <script src="inspector.js"></script>
</body>
</html>
```

スクリプト読込順序（厳守）: constants.js → eventEmitter.js → timers.js → utils.js → ulanziApi.js

CSSクラス: .uspi-wrapper, .uspi-item, .uspi-item-label, .uspi-item-value
ローカライズ: data-localize属性。値なし=要素テキストをキーとして使用、値あり=属性値をキーとして使用

JSパターン:
```javascript
$UD.connect('com.ulanzi.ulanzistudio.myplugin.myaction');

$UD.onConnected(conn => {
  // 動的UI描画
});

$UD.onAdd(message => {
  Utils.setFormValue(message.param, '#property-inspector');
});

$UD.onParamFromApp(message => {
  Utils.setFormValue(message.param, '#property-inspector');
});

document.querySelector('#property-inspector').addEventListener('change', () => {
  const params = Utils.getFormValue('#property-inspector');
  $UD.sendParamFromPlugin(params);
});
```

Property Inspectorのライフサイクル: ユーザーが別のボタンに切替えると破棄される。軽量かつステートレスに保つ。永続的なロジックはメインサービスに置く


## ローカライズ

対応言語（8言語）: zh_CN, zh_HK, en, ja_JP, de_DE, ko_KR, pt_PT, es_ES

JSONフォーマット:
```json
{
  "Name": "My Plugin",
  "Description": "My plugin description",
  "Actions": [
    {
      "Name": "Plugin Action",
      "Tooltip": "Run plugin action"
    }
  ],
  "Localization": {
    "Message": "メッセージ",
    "Save": "保存"
  }
}
```

- Name, Description, Actions: manifest表示のローカライズ
- Actions配列はmanifest.jsonのActions配列とインデックスで対応
- Localization: UI文字列のキーバリューペア

翻訳方法:
- HTML自動: data-localize属性
- JavaScript手動: $UD.t('key') — 翻訳文字列を返す。未発見時はキー自体を返す


## デプロイ・インストール

プラグインインストールディレクトリ: UlanziStudioのpluginsディレクトリに配置。ホストアプリが自動検出・manifest.jsonをパース・プラグインを読込

macOS: /Applications/Ulanzi Studio.app
シミュレータテスト: UlanziDeckSimulator/plugins/ に配置


## デバッグ

起動フラグ:
- --log: ログをファイルに書込
- --logLevel: ログ詳細度設定
- --pluginLoad: プラグインロードフック有効化
- --webRemoteDebug: HTML WebViewリモートデバッグ有効化。デフォルトポート9292
- --webRemotePort=<port>: WebViewデバッグポート変更
- --nodeRemoteDebug: Node.jsリモートデバッグ有効化。manifest.jsonのInspectフィールド必須
- --doubleClick: ダブルクリック検出有効化

macOSでの起動:
```bash
open /Applications/Ulanzi\ Studio.app --args --log --webRemoteDebug
```
注意: openコマンドではAccessibility権限が取得できず、ホットキー機能が動作しない場合がある。その場合は ./UlanziStudio を直接実行

HTMLプラグインデバッグ: --webRemoteDebug有効化後、ブラウザで localhost:9292 にアクセス（Chrome DevTools）
Node.jsプラグインデバッグ: manifest.jsonにInspect設定 → --nodeRemoteDebugで起動 → chrome://inspect でアクセス

ログファイル:
- macOS: ~/Library/Application Support/Ulanzi/UlanziDeck/logs/UlanziDeck_YYYYMMDD.xlog
- Windows: ~/AppData/Roaming/Ulanzi/UlanziStudio/logs/{mainServiceUUID}.log

シミュレータ:
```bash
cd UlanziDeckSimulator && npm install && npm start
```
アクセス: http://127.0.0.1:39069

シミュレータ制限事項:
- openview / openurl がローカルファイルにアクセスできない
- selectdialog はファイルパスの手動入力が必要
- アクションページは自動ロードされない（WebSocket競合防止）
- Node.jsサービスは手動起動が必要
- デスクトップアプリと挙動が異なる場合がある


## 制約・注意事項

1. アクションが非アクティブ時はsetSettings()で設定が保存されない
2. 同じアクションが複数キーに割当可能。contextで特定のキーインスタンスを識別すること。単一インスタンスを前提にしない
3. Property Inspectorはキー切替時に破棄される。ステートレスかつ軽量に保つ
4. Node.jsプラグインはRandomPortでポート衝突を回避。--inspectポートもプラグインごとにユニーク
5. UUIDセグメント数が重要。4セグメント=メインサービス、4超=アクション
6. SDKソースにタイポ: DIALEDOWN / DIALEUP（Eが余分）。ワイヤプロトコルでは dialdown / dialup
7. macOSでopenコマンド使用時にAccessibility権限の問題あり。直接 ./UlanziStudio で起動推奨
8. codeプロパティを持ち cmdType !== 'REQUEST' のメッセージは無視される
9. sendToPropertyInspector / sendToPlugin のデータはホストに保存されない。永続化が必要な場合は setSettings / sendParamFromPlugin を使用
10. Canvas描画フォント: "Source Han Sans SC"（ホストに内蔵）でシステムスタイルと一致
11. UlanziStudio背景色: #1e1f22（CSS変数: --uspi-bodybg）
12. HTML SDKのスクリプト読込順序は厳守
13. timers.js が window.setTimeout / window.setInterval を Web Worker ベースの実装に置換（WebView非表示時のUIスレッドブロッキング回避）
14. eventEmitter.js はワイルドカードパターン対応の軽量pub/sub実装（'*'で全イベント購読可能）
15. openUrl にURLクエリパラメータを含めない。param引数で渡す
16. エンコーダレイアウトの rect は配列 [x,y,w,h] とオブジェクト {x,y,w,h} の両方を受け付ける


## HTML SDKファイル構造

```
libs/
  css/
    uspi.css
  js/
    constants.js
    eventEmitter.js
    timers.js
    utils.js
    ulanziApi.js
  assets/
    *.svg
```

## Node.js SDKファイル構造

```
ulanzi-api/
  libs/
    constants.js
    randomPort.js
    utils.js
    ulanziApi.js
  apiTypes.d.ts
  index.js
```

index.js のエクスポート: UlanziApi (default), Utils, RandomPort


## TypeScript型定義（apiTypes.d.ts）

```typescript
interface ActionProps {
  uuid: string;
  actionid: string;
  key: string;
}

type Cmd = "run" | "add" | "clear" | "paramfromapp" | "paramfromplugin" |
           "setactive" | "state" | "openurl" | "openview" | "selectdialog" |
           "logMessage" | "hotkey" | "showAlert" | "sendToPropertyInspector" |
           "sendToPlugin" | "getSettings" | "setSettings" | "didReceiveSettings" |
           "setGlobalSettings" | "didReceiveGlobalSettings" | "getGlobalSettings" |
           "keydown" | "keyup" | "dialdown" | "dialup" | "dialrotate";

interface DeckRespDataBase<TCmd extends Cmd> {
  cmd: TCmd;
  code: number;
}

interface ParamRespData<TCmd extends Cmd> extends DeckRespDataBase<TCmd>, ActionProps {
  param?: Record<string, any> | null;
}

interface SetActiveRespData extends ParamRespData<'setactive'> {
  active: boolean;
}

interface SelectDialogRespData extends DeckRespDataBase<'selectdialog'> {
  cmdType: 'REQUEST';
  type: 'file' | 'folder';
  filter: string;
  path: string;
}
```


## hotkey() キー書式

ワイヤプロトコル:
```json
{
  "cmd": "hotkey",
  "uuid": "...",
  "key": "...",
  "actionid": "...",
  "keylist": "<hotkey-string>"
}
```
SDKメソッドの引数名は key だが、ワイヤ上は keylist フィールドで送信される。

macOS書式: Unicodeモディファイア記号 + キー
- ^ = Control
- ⌘ = Command
- ⌥ = Option/Alt
- ⇧ = Shift
- 例: ⌘C（Command+C）、⌘V（Command+V）、⌥⇧V（Option+Shift+V）

Windows書式: モディファイア名 + "+" + キー
- 例: Ctrl+C、Ctrl+Shift+V

注意: macOSでopenコマンド経由の起動ではAccessibility権限が取得できず、hotkey機能が動作しない場合がある。直接 ./UlanziDeck を実行すること


## openView() 詳細

```javascript
$UD.openView(url, width=200, height=200, x, y, param)
```
- url (string, 必須): ローカルHTMLパス。クエリパラメータはURL文字列に含めずparam引数で渡す
- width (number, 任意): ポップアップ幅px。デフォルト200
- height (number, 任意): ポップアップ高さpx。デフォルト200
- x (number, 任意): ウィンドウX位置。省略時は中央配置
- y (number, 任意): ウィンドウY位置。省略時は中央配置
- param (object, 任意): HTMLに渡すキーバリューパラメータ

ポップアップとメインサービス間に専用メッセージングチャネルはない。ポップアップ側でSDKを読込みsendToPlugin/sendToPropertyInspectorを使うか、独自WebSocket接続が必要。ポップアップは自身でwindow.close()を呼んで閉じる


## 実装パターン

ステート管理（per-keyインスタンス管理）:
全デモプラグイン共通のパターン。ACTION_CACHESディクショナリにcontextをキーとしてインスタンスを格納:

```javascript
const ACTION_CACHES = {}
$UD.connect('com.ulanzi.ulanzistudio.myplugin')

$UD.onAdd(jsn => {
  const context = jsn.context
  if (!ACTION_CACHES[context]) {
    ACTION_CACHES[context] = new MyAction(context)
  }
})

$UD.onRun(jsn => {
  const instance = ACTION_CACHES[jsn.context]
  if (!instance) $UD.emit('add', jsn)
  else instance.execute()
})

$UD.onSetActive(jsn => {
  const instance = ACTION_CACHES[jsn.context]
  if (instance) instance.setActive(jsn.active)
})

$UD.onClear(jsn => {
  if (jsn.param) {
    for (let i = 0; i < jsn.param.length; i++) {
      const context = jsn.param[i].context
      ACTION_CACHES[context].destroy()
      delete ACTION_CACHES[context]
    }
  }
})

$UD.onParamFromApp(jsn => { updateSettings(jsn) })
$UD.onParamFromPlugin(jsn => { updateSettings(jsn) })
```

setActive実装パターン: active=trueで描画を再開、falseで最後のアイコン更新後に送信を停止

タイマーパターン:
- HTML: timers.jsがwindow.setTimeout/setIntervalをWeb Workerベースに置換済み。通常通り使用可能。WebView非アクティブ時もスロットリングされない
- Node.js: ネイティブsetTimeout/setIntervalをそのまま使用

動的アイコン生成（HTML）:
```javascript
// Canvas直接描画（196x196がデフォルト）
const canvas = document.createElement('canvas')
canvas.width = 196
canvas.height = 196
const ctx = canvas.getContext('2d')
// ... 描画処理 ...
const icon = canvas.toDataURL('image/png')
$UD.setBaseDataIcon(context, icon, 'label text')
```

drawTextフォント設定:
- フォントファミリ: "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif
- フォントサイズ: 6文字以下=50px、7文字以上=40px（自動スケール）
- テキストは中央配置
- textLabel引数で左上(10,20)に24px太字のラベルを追加可能
- background="transparent" でclearRect使用（透過背景）

動的アイコン生成（Node.js）:
Node.jsにはCanvas APIがないため、SVG.js + svgdomでSVG描画 → base64変換:
```javascript
import { createSVGWindow } from 'svgdom'
import { SVG, registerWindow } from '@svgdotjs/svg.js'

const window = createSVGWindow()
const document = window.document
registerWindow(window, document)

const draw = SVG(document.documentElement).size(196, 196)
draw.rect(196, 196).fill('#000')
draw.text('Hello').font({ size: 40, weight: 'bold', fill: '#fff', anchor: 'middle' })
  .center(98, 98)
const svgContent = draw.svg()
const base64 = Buffer.from(svgContent).toString('base64')
$UD.setBaseDataIcon(context, 'data:image/svg+xml;base64,' + base64)
draw.clear()
```

ローカル画像のBase64化（Node.js）:
```javascript
import fs from 'fs'
const imgData = fs.readFileSync(Utils.getPluginPath() + 'resources/icon.png')
const base64 = 'data:image/png;base64,' + imgData.toString('base64')
$UD.setBaseDataIcon(context, base64)
```

永続化の2系統:
- paramパイプライン: sendParamFromPlugin / onParamFromApp。ホストが保存・Inspector間で中継。デモプラグインはこちらを使用
- settingsパイプライン: setSettings / getSettings / onDidReceiveSettings。セカンダリの永続化手段
- globalSettings: setGlobalSettings / getGlobalSettings。プラグイン全体で共有
- 注意: sendToPropertyInspector / sendToPlugin のデータはホストに保存されない（パススルーのみ）

HTML vs Node.js メインサービスの選択基準:
- HTML (app.html): Canvas描画、DOM操作、UIリッチな機能に向く。QWebEngineView（Chromium）で動作
- Node.js (app.js): ファイルアクセス、システム統合、外部API連携、複雑なロジックに向く。バンドルNode v20.18.0で動作
- Node.jsではRandomPortでInspector用WebSocketポート(49152-65535)を生成し、ws-port.jsに書出す必要がある
