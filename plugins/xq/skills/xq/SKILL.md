---
name: xq
description: "ターミナルでxqを使用し、X(Twitter)内の情報をGrokに調べさせる。「Xで調べて」「Xの反応」「Xでの評判」「Xのトレンド」「xqで〜」「ツイート探して」のような指示で発動。またはXにしかなさそうな情報や生の最新情報が必要と判断したときに発動。"
allowed-tools: Bash
---

# xq

Search X (Twitter) in natural language with the `xq` CLI, which calls xAI's
Responses API `x_search` tool directly (Grok-powered).
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

## Chat (persistent context)

For multi-turn research, use a named session so follow-ups keep prior context
without re-explaining it. The conversation is stored xAI-side (30-day retention)
and continued via `previous_response_id`, so each follow-up sends only the new
question (token-cheap):

```bash
xq chat <name> "first question"     # one-liner; creates the session on first use
xq chat <name> "follow-up that refers to 'それ' / 'that'"
xq chat list                        # sessions
xq chat show <name>                 # transcript
xq chat rm <name>                   # delete / reset an expired session
```

`--json` adds `session`, `turn_index`, `response_id`. One session = one
sequential conversation; for parallel work that must not mix context, use
distinct session names. Use one-shot `xq "..."` (no session) when no memory is
needed.

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

Credentials are resolved automatically from the `xai-oauth` token store (no X
API key, no setup). On `401`/`403` the token is stale/expired — tell the user
to re-auth:

```bash
hermes auth add xai-oauth
```

## Notes

- A query can take tens of seconds; allow a long timeout (`--timeout 240`).
- Prefer one well-formed `xq` call over looping; refine the query instead.
