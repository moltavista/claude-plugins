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
4. Read **`memory_context`** (also returned: what earlier sessions kept for this issue and its project), and `memory_search` the area you are about to touch (a package, a screen, a flaky test) before you change it.
5. Move the issue to the team's in-progress status with `save_issue` if it isn't there yet (`list_issue_statuses` for the names).

## While working

- **Plan**: keep a task list (Claude Code: TaskCreate/TaskUpdate or TodoWrite; Codex: `update_plan`). With a linked client session it becomes the session plan automatically; without one, send the full list with `session_plan` whenever it changes.
- **Activity**: linked sessions report tool calls by themselves. Add `session_activity` `thought` only for reasoning a human reviewer would want (a trade-off you took, a surprising finding). Without a linked session, also report notable `action`s (tests run, files changed).
- **Git**: branch `mst-12-short-slug`; mention the identifier in commit messages (`MST-12: fix redirect`). Linked sessions pick up commits, pushes, and the PR that a push reports or that `gh`/`tea`/`fj`/`glab` `pr create` opens. Add anything else with `session_link` (`branch`, `commit`, `pr`), in particular a PR opened through an API or the web UI. Link only your own PR: a linked PR can move the issue (merged → Done).
- **Blocked on a human choice?** Use the ask-human skill (`decision_ask`); don't guess on product, scope or risky calls.
- **Decisions worth keeping** (an architecture choice, a convention, a trade-off a later reader needs): read the accepted ones first with `adr_context`, then record yours as an ADR with `adr_save` (status `proposed`) on the team, or the workspace when it spans teams, linked to the issue (`links` kind `issue`). Cite ADRs by identifier (`MST-ADR-12`). A person confirms ADRs in the browser. Keep a repository's frozen historical decisions file unchanged: do not append, renumber or regenerate it. Do not reserve legacy decision numbers; migration and protocol reservations still use the workspace's coordination process. A repository mirror publishes native ADRs separately.
- **Previews**: to let people try a running app (a dev server, a UI change), run `fab expose <port> --json --comment-on MST-12 &` in the background. Its first line is `{url, id, expires_at}`, and it posts the link on the issue. Only the workspace's members can open it, after signing in, and they see whatever that port serves: expose only what the task needs, never a port serving secrets (`.env` files, debug consoles, database admin UIs), and stop the process when you are done, which closes the preview. It works when the workspace's Settings → Previews allows agents.
- **Human input** (`[mstep]` lines, `wait_events` results): follow the mstep-events skill.
- **Description edits**: `update_description` with `{find, replace}` edits, so concurrent human edits survive.

## Finish

1. Comment anything the humans should read in the thread with `save_comment` (what changed, how to verify, follow-ups).
2. **Keep what you learned** that a later session needs and that cost you time (a gotcha, a cause, a procedure): `memory_remember`, one fact or procedure per note, in the narrowest place (the issue, its project, the workspace, or your own agent memory). Fix a wrong or outdated note with `memory_correct` or `memory_forget` rather than adding a duplicate. Never secrets, code or git history.
3. Move the issue to the next status (e.g. In Review) with `save_issue`.
4. `session_end` with state `complete` and a short summary, or `error` with what blocked you.

A session ends only through `session_end` (or when this Claude Code / Codex session exits). After it ends, activity on it fails with `session_ended`; call `session_start` again if you resume the work.
