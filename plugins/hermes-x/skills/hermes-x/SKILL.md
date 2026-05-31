---
name: hermes-x
description: "HermesのGrok x_search経由でX(Twitter)を検索する。「Xで調べて」「Xで検索」「ツイート探して」「Xの反応」「X search」「hermes-x」「Xでの評判」「Xのトレンド」のような指示で発動する。"
allowed-tools: Bash
---

# hermes-x

Hermes の `x_search` ツールセットを使い、Grok 経由で X (Twitter) を検索する。

## 仕組み

```
Claude Code → hermes -t x_search -z "クエリ" → Grok x_search → X検索 → 結果要約
```

- メインモデル（エリス等）はそのまま。検索部分だけ Grok/xAI が担当
- xai-oauth のサブスク認証が必要（X API キーは不要）
- 読み取り専用（ポスト・いいね等の操作はできない。それは xurl の領域）

## 実行手順

1. ユーザーの検索意図からクエリを組み立てる
2. 以下のコマンドを実行:

```bash
hermes -t x_search -z "検索クエリ（具体的に書く。件数・URL付き等の指示も含める）"
```

3. 結果をユーザーに要約して返す

## クエリのコツ

- 具体的に書く: 「Claude Codeの最新の評判を3件、URL付きで」
- 言語指定可: 日本語・英語どちらでもOK
- 件数指定: 「5件」「top 3」等を含めると絞れる
- URL要求: 「URL付きで」と明示するとポストリンクが付く

## 例

```bash
# 特定トピックの最新動向
hermes -t x_search -z "Qwen3.6-27B-MTPの最新情報を5件、URL付きで要約して"

# プロダクトの評判調査
hermes -t x_search -z "Claude Codeの最近の反応を3件、URL付きで要約して"

# トレンド確認
hermes -t x_search -z "ローカルLLMの最新トレンドをXで5件探して"
```

## 注意

- `x_search` ツールセットが Hermes 側で有効である必要がある（`hermes tools enable x_search`）
- 処理に数十秒かかることがある。タイムアウトは長めに設定すること
