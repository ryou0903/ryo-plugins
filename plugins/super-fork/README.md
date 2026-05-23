# super-fork

Fork Claude Code sessions with more power than the built-in desktop fork.

Claude Desktop has a native "Fork" menu item, but it has limitations:

- ❌ Cannot fork remote-control sessions
- ❌ Cannot target a specific session by UUID from the CLI
- ❌ Cannot label forks for easy identification
- ❌ Cannot relocate a session to a different working directory

**super-fork** fills the gap with a single `/super-fork` command.

## Installation

```bash
/plugin marketplace add ryou0903/super-fork
/plugin install super-fork@ryou0903
```

## Usage

```bash
/super-fork                                    # fork the current session
/super-fork <session-uuid>                     # fork a specific session
/super-fork --name "label"                     # fork with a label ([s-fork] prefix added)
/super-fork --cwd ~/new/path                   # fork into a different project directory
/super-fork --cwd ~/new/path --name "label"    # relocate + label
/super-fork --list                             # list labeled forks
```

On success:

```
✅ Forked → 73a18acb-164f-4538-9724-31a90db556b1
   source:  36495033-7039-4b47-a482-7518a09da7a1
   cwd:     .../cn-nanoclaw → .../cn-claw
   resume:  cd .../cn-claw && claude --resume 73a18acb-...
   label:   [s-fork] my label  (desktop sidebar + backup)
```

## Features

### Labels (`--name`)

Labeled forks appear in the Claude Desktop sidebar with a `[s-fork]` prefix. Labels are also saved to `~/.claude/super-fork-labels.json` as a backup in case the desktop app loses or rewrites metadata.

### Directory relocation (`--cwd`)

Move a session to a different project folder. The target directory is auto-created if it doesn't exist. Useful when renaming projects or branching experiments into isolated directories.

### Fork awareness (automatic)

A `SessionStart` hook detects forked sessions by comparing the filename UUID against the embedded `sessionId` in the conversation history. When a mismatch is found, the resumed Claude is told it's a fork — preventing identity confusion and accidental interference with the original session's state.

## How it works

Claude Code stores each session as a JSONL file at `~/.claude/projects/<cwd-encoded>/<uuid>.jsonl`. A fork is a byte-level copy (`shutil.copy2`) to a new file — the same approach Claude Desktop uses internally. The CLI treats the filename as the authoritative session ID.

## Roadmap

- ✅ Byte-level fork
- ✅ `--name` labels with desktop sidebar integration
- ✅ `--cwd` directory relocation with auto-create
- ✅ `--list` labeled fork listing
- ✅ Fork-awareness `SessionStart` hook
- 🔲 Lineage-extraction fork (split a branched session into single-lineage files)

## License

MIT
