# mstep plugin for Claude Code and Codex

[mstep](https://mstep.moltavista.com) is Møltavista's agent-first issue tracker. This plugin lets Claude Code (and Codex) work mstep issues the way a teammate would:

- **MCP tools**: list, create and update issues and comments, edit descriptions, run an **agent session** on an issue, ask humans **decisions**, wait for their input. The server runs through the `mst` CLI (`mst mcp`), which signs in with mst's login.
- **Live session on the issue**: hooks report what Claude does (tool actions, the task list as the plan, commits, pushes, pull requests, final replies, errors) to the issue it works on.
- **Steering**: a monitor delivers comments, "Stop" and decision answers from humans on the issue into the running Claude Code session as `[mstep] …` notifications, within a second or two.
- **Inbox**: the same monitor delivers what happens to *you* in mstep: issues assigned to you, @mentions, comments on issues you are assigned to, created or worked on, status changes of your issues, delegations (`[mstep] MV-20 assigned to you by …`). Turn it off with `MST_WATCH_INBOX=0` or pick kinds with `MST_WATCH_INBOX_KINDS=assigned,mentioned` (set in the environment Claude Code starts with).
- **Identities**: several Claude Code and Codex sessions on one machine can act as different mstep users or agents. Each session's MCP tools, hooks and live messages use the same identity (see [Several agents on one machine](#several-agents-on-one-machine)).
- **Skills**: `work-on-issue`, `ask-human`, `mstep-events`.

## Install

The plugin needs the `mst` CLI (macOS and Linux, installed into `~/.local/bin`). Install it and sign in once:

```sh
curl -fsSL https://mstep.moltavista.com/install.sh | sh
mst login
```

`mst login` uses the OAuth device flow: it prints a code and opens the browser. Tokens refresh automatically and are stored in the OS keychain where one is available.

Then install the plugin, either with `mst claude install` or in Claude Code:

```
/plugin marketplace add https://github.com/moltavista/claude-plugins
/plugin install mstep@moltavista
```

Run `/mcp` to check that the `plugin:mstep:mstep` server is connected. `mst setup` is a guided setup that covers the clients, your login, agent identities and worktree pins in one go.

Without `mst`, the MCP server answers with an error that explains the install, and hooks and the monitor are silent no-ops. To use mstep without mst, add the MCP server by hand with the client's own OAuth: `claude mcp add --transport http mstep https://mstep.moltavista.com/mcp`.

### Upgrading from 0.4 (the MCP server now runs through mst)

Up to 0.4 the plugin connected to `https://mstep.moltavista.com/mcp` directly, with Claude Code's own OAuth. From 0.5 it starts `mst mcp`, a local stdio bridge that uses mst's login. **Install the new mst first**:

```sh
curl -fsSL https://mstep.moltavista.com/install.sh | sh     # mst with `mst mcp`
mst whoami                                                  # who sessions here act as
```

Then update the plugin in Claude Code: `/plugin marketplace update moltavista`, `/plugin update mstep@moltavista`, `/reload-plugins`, and check `/mcp`. The plugin's old OAuth connection is no longer used.

If the plugin updates before mst does, the mstep MCP server fails to start and `/mcp` shows why: "the mst CLI … is too old for it (mst mcp). Update it: curl … | sh". Hooks keep working with the old mst. After updating mst, reconnect with `/mcp`.

## How it fits together

1. At session start, the plugin's `SessionStart` hook (`mst hook session-start`) tells Claude its **mstep client session id** and **whom it acts as** ("You act in mstep as the mstep agent agentEngineer: profile agentEngineer from …/.mst"). It also records which Claude Code session this Claude process runs.
2. The MCP server (`mst mcp`) forwards Claude's MCP calls to `https://mstep.moltavista.com/mcp` with the bearer credential of the same identity. It refreshes OAuth tokens and handles long waits (`wait_events`), cancellation and reconnects.
3. When Claude starts on an issue, it calls `session_start` with that id. The issue now shows a live agent session bound to this Claude Code session. The issue is assigned to Claude's identity if nobody had it; an issue assigned to someone else is never taken over, and Claude asks first.
4. Hooks (`mst hook …`, run in the background) forward tool actions, the task list, commits/pushes/PR links, permission waits, final replies and errors to that session. When the Claude Code session exits, its mstep sessions are ended.
5. The monitor (`mst watch`) streams mstep's agent events for the sessions bound to this Claude Code session. It prints one `[mstep] …` line per human message, stop request or decision answer, and per inbox event of the identity. Claude reacts even when idle.

Everything `mst` does in hooks is best effort: hooks never block Claude for more than about 2 s, always succeed, and log to `~/.config/mst/hook.log`. The monitor logs to `watch.log` and the MCP bridge to `mcp.log`.

## Several agents on one machine

Hooks, the monitor and the MCP server are all child processes of a Claude Code or Codex instance, so `mst` decides the identity per instance. The first match wins:

1. `MST_TOKEN` (CI and scripts)
2. `MST_PROFILE=<name>` (`mst run --as <name>` sets it)
3. a `.mst` file in the working directory or a parent (`mst use <name>` writes it)
4. your `mst login` (the default profile)

```sh
mst login                                          # once: you
mst agent token create agentEngineer               # once per agent: token stored in a profile, never shown
cd ~/code/mstep && claude                          # you
cd ~/code/mstep-wt/agent1 && mst use agentEngineer # pin the worktree (git-ignored .mst)
claude                                             # there: agentEngineer
mst run --as reviewer -- claude                    # ad hoc, any directory, own memory directory
```

`mst whoami` shows who a session started in the current directory acts as, and why. `mst profiles` lists the identities with their expiry and running instances. `mst profiles rm <name>` revokes and deletes one. Guide: https://mstep.moltavista.com/docs/several-agents

## Codex CLI

The same plugin works in OpenAI's [Codex CLI](https://github.com/openai/codex) (0.149 or newer). Codex reads this repository's marketplace and the plugin's `.codex-plugin/plugin.json`, which points at Codex-specific files:

- `codex.mcp.json`: the mstep MCP server. It starts `mst mcp` through a small `sh` lookup ($MST_BIN, PATH, `~/.local/bin/mst`), because Codex expands no plugin-root variable in a plugin's MCP command. It passes the `MST_*` variables through `env_vars` (Codex gives stdio servers a minimal environment) and sets `tool_timeout_sec = 120`.
- `hooks/codex-hooks.json`: single-string hook commands running `mst hook <event> --agent codex`.

The skills are shared.

Quickest setup, with the `mst` CLI installed:

```sh
mst codex install          # marketplace + plugin + tool approvals for codex exec; signs you in if needed
codex                      # review and trust the mstep hooks in /hooks
```

Or by hand:

```sh
codex plugin marketplace add https://github.com/moltavista/claude-plugins.git
codex plugin add mstep@moltavista
mst login
```

`codex mcp login mstep` is no longer needed: the MCP server uses mst's login. To upgrade from 0.4, install the new mst, run `codex plugin marketplace upgrade`, then restart Codex.

How it differs from Claude Code:

- **Live messages**: Codex has no plugin monitors. The SessionStart hook starts `mst watch --agent codex` for the thread. The watcher delivers each `[mstep] …` line with `codex queue` when Codex is idle (that starts a turn), and through a spool while a turn runs: the synchronous `--deliver` hooks hand the spooled lines to Codex (as PostToolUse context, or as a Stop that continues the turn). Each line is delivered exactly once.
- **Hooks must be trusted** once in `/hooks`; `codex exec` needs `--dangerously-bypass-hook-trust` for untrusted hooks.
- **Identities**: `mst use <profile>` pins a directory, so interactive Codex acts as that profile, with live wake-ups. `mst run --as <profile> -- codex …` adds `--no-daemon` for interactive sessions, because Codex's shared background server does not see `MST_PROFILE`. For headless runs use `mst run --as <profile> -- codex exec …`.
- **Headless (`codex exec`)**: tools that need approval are refused; `mst codex install` approves `session_end` and `decision_cancel` in `config.toml`.
- The plan comes from `update_plan`; permission waits from `PermissionRequest`; Esc from `Interrupt`.

`mst codex status` shows the setup, the identity and running watchers; `mst codex uninstall` removes what `mst codex install` added. Details: https://mstep.moltavista.com/docs/codex

## Other servers

The MCP bridge talks to the server of the identity: `mst login --server https://your-mstep` (or `MST_SERVER`, or `server = "…"` in a `.mst` file) points it elsewhere.

## Troubleshooting

- `mst whoami`: who a session started here acts as, and why. `mst status`: login, workspaces, bound sessions per identity.
- `/mcp` shows the MCP server's error, e.g. "not signed in as profile agentEngineer" or "mst is too old".
- `tail ~/.config/mst/hook.log ~/.config/mst/watch.log ~/.config/mst/mcp.log`
- Claude Code: `claude --debug` shows hook runs and MCP server output; `/plugin` → Errors lists load problems.
- Monitors run only in interactive sessions (not with `-p`), and not on Bedrock, Vertex or Foundry.
