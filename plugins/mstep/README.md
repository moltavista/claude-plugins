# mstep plugin for Claude Code

[mstep](https://mstep.moltavista.com) is Møltavista's agent-first issue tracker. This plugin lets Claude Code work mstep issues the way a teammate would:

- **MCP tools** (`https://mstep.moltavista.com/mcp`): list, create and update issues and comments, edit descriptions, run an **agent session** on an issue, ask humans **decisions**, wait for their input.
- **Live session on the issue**: with the `mst` CLI installed, hooks report what Claude does (tool actions, the task list as the plan, commits, pushes, pull requests, final replies, errors) to the issue it works on.
- **Steering**: a monitor delivers comments, "Stop" and decision answers from humans on the issue into the running Claude Code session as `[mstep] …` notifications, within a second or two.
- **Inbox**: the same monitor delivers what happens to *you* in mstep: issues assigned to you, @mentions, comments on issues you are assigned to, created or worked on, status changes of your issues, delegations (`[mstep] MV-20 assigned to you by …`). Turn it off with `MST_WATCH_INBOX=0` or pick kinds with `MST_WATCH_INBOX_KINDS=assigned,mentioned` (set in the environment Claude Code starts with).
- **Skills**: `work-on-issue`, `ask-human`, `mstep-events`.

## Install

In Claude Code:

```
/plugin marketplace add https://git.teixos.net/moltavista/claude-plugins
# while the moltavista org is private, org members use SSH instead:
# /plugin marketplace add git@git.teixos.net:moltavista/claude-plugins.git
/plugin install mstep@moltavista
```

The first mstep tool call opens a browser to sign in (OAuth through Møltavista's login; Claude Code registers itself). Run `/mcp` to check the `plugin:mstep:mstep` server.

For live session reporting and steering, install the `mst` CLI (macOS and Linux, into `~/.local/bin`) and sign in once:

```sh
curl -fsSL https://mstep.moltavista.com/install.sh | sh
mst login
```

`mst login` uses the OAuth device flow (it prints a code and opens the browser) and refreshes its token automatically. For headless agents: `mst login --token mst_…` with an agent or personal token from mstep's settings. `mst status` shows the login and which Claude Code sessions are bound to issues.

Without `mst` the plugin still works (MCP tools and skills); hooks and the monitor are then silent no-ops, and Claude can wait for human input with the `wait_events` tool.

## How it fits together

1. At session start, the plugin's `SessionStart` hook (`mst hook session-start`) tells Claude its **mstep client session id** and records which Claude Code session this Claude process runs.
2. When Claude starts on an issue it calls `session_start` with that id. The issue now shows a live agent session bound to this Claude Code session, and is assigned to you if nobody had it (an issue assigned to someone else is never taken over: Claude asks first).
3. Hooks (`mst hook …`, run in the background) forward tool actions, the task list, commits/pushes/PR links, permission waits, final replies and errors to that session. When the Claude Code session exits, its mstep sessions are ended.
4. The monitor (`mst watch`) streams mstep's agent events for the sessions bound to this Claude Code session and prints one `[mstep] …` line per human message, stop request or decision answer, and per inbox event of the signed-in user. Claude reacts even when idle.

Everything `mst` does is best effort: hooks never block Claude for more than ~2 s, always succeed, and log to `~/.config/mst/hook.log` (`watch.log` for the monitor).

## Other servers

The MCP server URL is fixed to `https://mstep.moltavista.com/mcp`. For another mstep server, add it yourself (`claude mcp add --transport http mstep https://your-mstep/mcp`) and point `mst` at it with `mst login --server https://your-mstep` (or `MST_SERVER`).

## Troubleshooting

- `mst status`: login, workspaces, bound sessions.
- `tail ~/.config/mst/hook.log ~/.config/mst/watch.log`
- Claude Code: `claude --debug` shows hook runs; `/plugin` → Errors lists load problems.
- Monitors run only in interactive sessions (not with `-p`), and not on Bedrock, Vertex or Foundry.
