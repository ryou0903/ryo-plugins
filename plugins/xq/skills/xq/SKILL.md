---
name: xq
description: "xqコマンドでX(Twitter)を自然言語検索する（xAIのx_searchを直接叩くGrok製。hermes-x後継）。「Xで調べて」「Xで検索」「ツイート探して」「Xの反応」「Xでの評判」「Xのトレンド」「X search」「xq」のような指示で発動。"
allowed-tools: Bash
---

# xq

Search X (Twitter) in natural language with the `xq` CLI, which calls xAI's
Responses API `x_search` tool directly (Grok-powered). Successor to `hermes-x`.
Read-only: search and summarize, no posting/liking.

## Usage

One-liner, natural language. Be specific — include count, "with URLs", and
language when relevant:

```bash
xq "Claude Code's recent reception on X, 3 posts with URLs"
```

Structured output for chaining/parsing:

```bash
xq --json "latest @xai post, 1 item with URL"
```

Default text output is a `回答:` summary plus a `引用:` list of source URLs.
`--json` returns `{success, answer, citation_urls, mode, ...}`.

## Modes (optional system prompt)

A mode injects a system prompt to steer the answer. Default off. Use the
per-call flags — they are stateless (write nothing) and parallel-safe:

```bash
xq --mode concise-ja "..."              # named preset (concise-ja, sourced, timeline)
xq --mode-text "answer in 3 lines" "..."  # inline one-shot prompt
xq --no-mode "..."                       # force plain Grok
xq mode list --json                      # discover available modes
```

## Auth & errors

Credentials are resolved automatically from Hermes' `xai-oauth` (no X API key,
no setup). On `401`/`403` the token is stale/expired — tell the user to re-auth:

```bash
hermes auth add xai-oauth
```

## Notes

- A query can take tens of seconds; allow a long timeout (`--timeout 240`).
- Prefer one well-formed `xq` call over looping; refine the query instead.
