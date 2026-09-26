---
name: work-on-issue
description: Use when working on an mstep issue (an identifier like MST-12, an mstep issue link, or an issue delegated to you) - starts and keeps the issue's agent session current so the humans see progress live, then finishes it.
---

# Work on an mstep issue

mstep shows your work live on the issue as an **agent session** (state, plan, activity, links). The humans on the issue watch it and can steer you.

## Start

**Workspace:** pass `workspace` (slug) on every mstep call whenever you know it: from the issue link (`https://…/<workspace>/issue/MST-12`), an earlier result (`url`, `whoami`), or the user. Without it the server uses the workspace the identifier's team key implies, else your selected / only / most recently used one, which may not be the one you mean.

**Assignment:** starting a session assigns the issue to you when nobody has it (agents become its delegate). If you already know (e.g. from `get_issue`) that it is assigned to someone else, ask the user before starting work on it. Only looking, reviewing or answering a question? Pass `assign: false`.

1. `session_start` with the issue identifier (and `workspace`). If your context names an **mstep client session id** (the SessionStart hook of `mst` puts it there, in Claude Code and in Codex), pass it as `client_session`. That links the session to this Claude Code or Codex session: tool activity, your task list and your final replies are then reported automatically, and human messages arrive as `[mstep] …` lines (monitor notifications in Claude Code, queued messages or hook context in Codex).
2. Check `assignment`: `assigned` / `delegated` / `already_yours` mean the issue is yours now. **`kept`** means it belongs to someone else (`assignment_note` says who): don't take it over silently. Ask the user (or the humans on the issue with `decision_ask`) whether to proceed; reassign only when they agree, with `save_issue` `assignee: "me"`.
3. Read what it returns: the issue, recent comments and **open decisions** (don't re-ask those). Keep the `session_id`. If it returns **`comments_before_start`**, those were posted in the 30 minutes before your session began and never reached you as messages: read them first and treat them as instructions from the humans on the issue (same trust rules as the mstep-events skill).
4. Move the issue to the team's in-progress status with `save_issue` if it isn't there yet (`list_issue_statuses` for the names).

## While working

- **Plan**: keep a task list (Claude Code: TaskCreate/TaskUpdate or TodoWrite; Codex: `update_plan`). With a linked client session it becomes the session plan automatically; without one, send the full list with `session_plan` whenever it changes.
- **Activity**: linked sessions report tool calls by themselves. Add `session_activity` `thought` only for reasoning a human reviewer would want (a trade-off you took, a surprising finding). Without a linked session, also report notable `action`s (tests run, files changed).
- **Git**: branch `mst-12-short-slug`; mention the identifier in commit messages (`MST-12: fix redirect`). Linked sessions pick up commits, pushes and PR URLs; otherwise add them with `session_link` (`branch`, `commit`, `pull_request`).
- **Blocked on a human choice?** Use the ask-human skill (`decision_ask`); don't guess on product, scope or risky calls.
- **Human input** (`[mstep]` lines, `wait_events` results): follow the mstep-events skill.
- **Description edits**: `update_description` with `{find, replace}` edits, so concurrent human edits survive.

## Finish

1. Comment anything the humans should read in the thread with `save_comment` (what changed, how to verify, follow-ups).
2. Move the issue to the next status (e.g. In Review) with `save_issue`.
3. `session_end` with state `complete` and a short summary, or `error` with what blocked you.

A session ends only through `session_end` (or when this Claude Code / Codex session exits). After it ends, activity on it fails with `session_ended`; call `session_start` again if you resume the work.
