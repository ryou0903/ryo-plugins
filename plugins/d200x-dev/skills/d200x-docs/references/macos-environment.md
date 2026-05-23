# Ulanzi Studio macOS環境リファレンス

Ulanzi Studio バージョン: 3.0.15
バンドルNode.js: v20.18.0
アプリパス: /Applications/Ulanzi Studio.app
実行バイナリ: /Applications/Ulanzi Studio.app/Contents/MacOS/UlanziDeck（Qt製）
バンドルNode: /Applications/Ulanzi Studio.app/Contents/MacOS/NodeJS/node


## ディレクトリ構造

ユーザーデータルート: ~/Library/Application Support/Ulanzi/UlanziDeck/

```
UlanziDeck/
  config/
    device.json               接続デバイスのレイアウト定義
    device_source.json         デバイスレジストリ（現在のD200X）
    device_type_source.json    全デバイスタイプのレイアウト（D200, D200H, D200X, Dial, 5x3）
    setting.json               輝度、フォント、現在のデバイス/プロファイル
    setting_source.json        マルチデバイス設定
  Plugins/                     ユーザーインストールプラグイン
  System/
    Plugins/                   組み込みシステムプラグイン
    Images/ScreenSave/
  ProfilesV2/
    {uuid}.ulanziProfile/
      manifest.json            プロファイルメタデータ（名前、デバイス、ページリスト）
      icon_default_profile.png
      Profiles/
        {uuid}/                ページごとに1ディレクトリ
          manifest.json        ページレイアウト（"row_col"キーでアクション定義）
          Files/
          Images/              ページ用アイコンアセット
  Images/                      ユーザーアップロード画像
  Icons/                       ユーザーアップロードアイコン
  Marketplace/
    user.json                  暗号化されたマーケットプレイス認証
    temp/
  logs/
    UlanziDeck_YYYYMMDD.xlog   日次ログ
    UlanziDeck.mmap3            メモリマップドログ
  process/
    process.txt                実行中プラグインプロセスのPID
  u-cly.db                     SQLiteデータベース
  version.txt                  バージョン情報
  defProfile/                  デフォルトプロファイル
  bak/                         バックアップ
  TempData/
  SendZip/
```


## プラグインインストールパス

ユーザープラグイン: ~/Library/Application Support/Ulanzi/UlanziDeck/Plugins/
システムプラグイン: ~/Library/Application Support/Ulanzi/UlanziDeck/System/Plugins/

プラグインフォルダを Plugins/ に置けばUlanzi Studioが自動検出する。


## インストール済みプラグイン

ユーザープラグイン（3個）:
- com.ulanzi.APIRequest.ulanziPlugin
- com.ulanzi.netbluemac.ulanziPlugin（Bluetooth/WiFi）
- com.ulanzi.websocketMessage.ulanziPlugin

システムプラグイン（7個）:
- com.ulanzi.deck.multiaction（マルチアクション/マクロ）
- com.ulanzi.deck.page（ページ切替）
- com.ulanzi.deck.sound（サウンド再生）
- com.ulanzi.deck.system（Open, Close, Website, Text, Hotkey, Multimedia, Hotkey Switch）
- com.ulanzi.dial.system（ダイアルシステム）
- com.ulanzi.lightmaster.ulanziPlugin（照明制御）
- com.ulanzi.obsstudio.ulanziPlugin（OBS Studio連携、18アクション）


## 接続デバイス

デバイス: Ulanzi Deck D200X ("Creative Deck")
モデルUUID: 02d04a045u3674975
device.jsonでのレイアウト: 5列 x 3行（15ポジション）


## プロファイル格納

パス: ~/Library/Application Support/Ulanzi/UlanziDeck/ProfilesV2/
構造: UUID名のフォルダ内にmanifest.jsonとページデータ
ページレイアウト: アクションが "row_col" キー（例: "0_2" = Row0, Col2）で定義される


## 設定ファイル

plistファイル:
- ~/Library/Preferences/com.ulanzi.UlanziDeck.plist
- ~/Library/Preferences/com.ulanzizhixin.UlanziDeck.plist
- ~/Library/Preferences/ulanzi.UlanziStudio.plist

キャッシュ:
- ~/Library/Caches/Ulanzi Studio/（Qtパイプラインキャッシュのみ）


## Node.jsプラグイン起動方法

ホストアプリがバンドルNodeで起動:
```
/Applications/Ulanzi Studio.app/Contents/MacOS/NodeJS/node {codepath} 127.0.0.1 {port} {language}
```
引数: process.argv[2]=アドレス, process.argv[3]=ポート, process.argv[4]=言語


## デバッグ起動

```bash
open /Applications/Ulanzi\ Studio.app --args --log --webRemoteDebug
```
注意: openコマンドではAccessibility権限が取得できずhotkey機能が動作しない場合あり。
代替: /Applications/Ulanzi\ Studio.app/Contents/MacOS/UlanziDeck を直接実行
