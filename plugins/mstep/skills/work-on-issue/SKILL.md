---
name: work-on-issue
description: Use when working on an mstep issue (an identifier like MST-12, an mstep issue link, or an issue delegated to you) - starts and keeps the issue's agent session current so the humans see progress live, then finishes it.
---

# Work on an mstep issue

mstep shows your work live on the issue as an **agent session** (state, plan, activity, links). The humans on the issue watch it and can steer you.

## Start

1. `session_start` with the issue identifier. If your context names an **mstep client session id** (the plugin's SessionStart hook puts it there), pass it as `client_session`. That links the session to this Claude Code session: tool activity, your task list and your final replies are then reported automatically, and human messages arrive as `[mstep] …` notifications.
2. Read what it returns: the issue, recent comments and **open decisions** (don't re-ask those). Keep the `session_id`.
3. Move the issue to the team's in-progress status with `save_issue` if it isn't there yet (`list_issue_statuses` for the names).

## While working

- **Plan**: keep a task list (TaskCreate/TaskUpdate or TodoWrite). With a linked client session it becomes the session plan automatically; without one, send the full list with `session_plan` whenever it changes.
- **Activity**: linked sessions report tool calls by themselves. Add `session_activity` `thought` only for reasoning a human reviewer would want (a trade-off you took, a surprising finding). Without a linked session, also report notable `action`s (tests run, files changed).
- **Git**: branch `mst-12-short-slug`; mention the identifier in commit messages (`MST-12: fix redirect`). Linked sessions pick up commits, pushes and PR URLs; otherwise add them with `session_link` (`branch`, `commit`, `pull_request`).
- **Blocked on a human choice?** Use the ask-human skill (`decision_ask`); don't guess on product, scope or risky calls.
- **Human input** (`[mstep]` lines, `wait_events` results): follow the mstep-events skill.
- **Description edits**: `update_description` with `{find, replace}` edits, so concurrent human edits survive.

## Finish

1. Comment anything the humans should read in the thread with `save_comment` (what changed, how to verify, follow-ups).
2. Move the issue to the next status (e.g. In Review) with `save_issue`.
3. `session_end` with state `complete` and a short summary, or `error` with what blocked you.

A session ends only through `session_end` (or when this Claude Code session exits). After it ends, activity on it fails with `session_ended`; call `session_start` again if you resume the work.
