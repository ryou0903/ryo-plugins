# cmux ブラウザ自動化

`cmux browser` コマンドグループで提供。ナビゲーション、DOM操作、ページ検査、JavaScript実行、セッション管理が可能。

## コマンド分類

### ナビゲーション
`identify`, `open`, `open-split`, `navigate`, `back`, `forward`, `reload`, `url`, `focus-webview`, `is-webview-focused`

### 待機
`wait` — セレクタ、テキスト、URL、読み込み状態、JavaScript条件での待機

### DOM操作
`click`, `dblclick`, `hover`, `focus`, `check`, `uncheck`, `scroll-into-view`, `type`, `fill`, `press`, `keydown`, `keyup`, `select`, `scroll`

### 検査
`snapshot`, `screenshot`, `get`, `is`, `find`, `highlight`

### JavaScript実行
`eval`, `addinitscript`, `addscript`, `addstyle`

### その他
`frame`, `dialog`, `download`, `tab`, `console`, `errors`, `cookies`, `storage`, `state`

## 使用例

### ナビゲーション
```bash
cmux browser open https://example.com
cmux browser surface:2 navigate https://example.org/docs
```

### 待機
```bash
cmux browser wait "#content"
cmux browser wait --text "Loading complete"
cmux browser wait --url "*/dashboard"
```

### フォーム操作
```bash
cmux browser surface:2 fill "#email" --text "ops@example.com"
cmux browser surface:2 click "button[type='submit']"
```

### 検査・デバッグ
```bash
cmux browser snapshot
cmux browser screenshot
cmux browser console
cmux browser errors
```

### セッション管理
```bash
cmux browser state save mystate
cmux browser state load mystate
```

## ブラウザ関連ショートカット

- `⌘⇧L` — ブラウザを開く
- `⌘L` — アドレスバーフォーカス
- `⌥⌘D` — 右にブラウザ分割
- `⌥⌘⇧D` — 下にブラウザ分割
- `⌥⌘I` — 開発者ツール
- `⌥⌘C` — JavaScriptコンソール
