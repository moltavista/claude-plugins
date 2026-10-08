---
name: ask-human
description: Use when mstep work is blocked on a choice only a human should make (product behaviour, scope, naming, risky or irreversible steps, missing access) - asks a structured mstep decision with a recommendation instead of guessing, and handles the answer.
---

# Ask the humans (mstep decisions)

A **decision** is a structured question on the issue. The issue moves to "Needs Human", the recipients answer in mstep (web or phone), and the answer comes back to you.

## When

Ask when the answer changes what you build and you cannot find it in the issue, its comments, the code or the docs: product behaviour, scope cuts, API or naming choices others depend on, destructive or irreversible steps, credentials or access you lack.

Don't ask for things you can look up or safely decide and mention in your summary, and never to approve your own tool permissions: permission prompts belong to the person at this terminal.

## How

Call `decision_ask`:

- `session_id` from `session_start` (shows the question in the session), or `issue` for an issue-level question.
- `question`: one sentence. `context`: short markdown with what you found and the trade-offs.
- `kind`: `single` (pick one), `multi`, `yes_no` or `free_text`. For single/multi give 2-5 `options`, each a short `label` plus a `description` of its consequences.
- `recommended` (an option label) and `confidence` (0-1): always give your recommendation, the humans answer faster.
- `recipients` only when a specific person or team must decide (names, emails or team keys); default is anyone with access.
- `wait` (default true) holds the call until someone answers. In Claude Code, after about two minutes the call moves to the background: keep working on anything that does not depend on the answer; the result arrives as a task notification. In Codex, pass `max_wait_seconds` below the MCP tool timeout (e.g. 100; the plugin sets 120 s). If it returns `status: "pending"`, continue and later call `decision_wait` with the id (same limit in Codex).

## When the answer arrives

- The same answer can reach you twice: as the tool result and as an `[mstep] decision on MST-12 answered by …` line (same decision id). Act on it once.
- Follow the chosen option; read any free-text note, it can refine or override the options.
- `canceled`: the question is moot. Re-read the issue and comments, re-plan, and only ask again if you are still blocked.
- Don't ask the same question again while it is open (`get_issue` lists open decisions); `decision_cancel` one you no longer need.
