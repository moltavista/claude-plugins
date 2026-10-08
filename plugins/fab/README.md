# fabbrica plugin for Claude Code and Codex
The `fab` entry is preferred for new installs. `mstep` remains a compatibility alias for one cycle. Install only one entry to avoid duplicate hooks and watchers. Both prefer `fab` and fall back to compatible `mst`; `FAB_*` settings take precedence while legacy `MST_*` settings and `.mst` pins remain supported. Existing `~/.config/mst` profiles are read in place when there is no new fab configuration. The MCP namespace and `[mstep]` event prefix remain unchanged.

[fabbrica](https://fab.moltavista.com) is Møltavista's agent-first issue tracker. This plugin lets Claude Code (and Codex) work mstep issues the way a teammate would:

- **MCP tools**: list, create and update issues and comments, edit descriptions, run an **agent session** on an issue, ask humans **decisions**, wait for their input. The server runs through the `fab` CLI (`fab mcp`), which signs in with mst's login.
- **Live session on the issue**: hooks report what Claude does (tool actions, what is running right now, the task list as the plan, commits, pushes, pull requests, prompts typed at the terminal, compactions, loaded instruction files, final replies, errors) to the issue it works on. Credentials in what they report are redacted. Prompts typed at the terminal appear on the issue for everyone who can see it (a shared issue's audience and exports included); `FAB_REPORT_PROMPTS=0` keeps a machine's prompts local. `FAB_UPLOAD_IMAGES=0` keeps images local.
- **Steering**: a monitor delivers comments, "Stop" and decision answers from humans on the issue into the running Claude Code session as `[mstep] …` notifications, within a second or two.
- **Inbox**: the same monitor delivers what happens to *you* in mstep: issues assigned to you, @mentions, comments on issues you are assigned to, created or worked on, status changes of your issues, delegations (`[mstep] MV-20 assigned to you by …`). Turn it off with `FAB_WATCH_INBOX=0` or pick kinds with `FAB_WATCH_INBOX_KINDS=assigned,mentioned` (set in the environment Claude Code starts with).
- **Identities**: several Claude Code and Codex sessions on one machine can act as different mstep users or agents. Each session's MCP tools, hooks and live messages use the same identity (see [Several agents on one machine](#several-agents-on-one-machine)).
- **Skills**: `work-on-issue`, `ask-human`, `mstep-events`.

## Install

The plugin needs the `fab` CLI (or compatible `mst` during the transition) (macOS and Linux, installed into `~/.local/bin`). Install it and sign in once:

```sh
curl -fsSL https://fab.moltavista.com/install.sh | sh
fab login                  # use mst login if the installer still supplies mst
```

`fab login` uses the OAuth device flow: it prints a code and opens the browser. Tokens refresh automatically and are stored in the OS keychain where one is available.

Then install the plugin, either with `fab claude install` or in Claude Code:

```
/plugin marketplace add https://github.com/moltavista/claude-plugins
/plugin install fab@moltavista
```

Run `/mcp` to check that the `plugin:fab:mstep` server is connected. `fab setup` is a guided setup that covers the clients, your login, agent identities and worktree pins in one go.

Without either `fab` or compatible `mst`, the MCP server answers with an error that explains the install, and hooks and the monitor are silent no-ops. To use fabbrica without either CLI, add the MCP server by hand with the client's own OAuth: `claude mcp add --transport http mstep https://fab.moltavista.com/mcp`.

### Upgrading from 0.4 (the MCP server now runs through mst)

Up to 0.4 the plugin connected to `https://mstep.moltavista.com/mcp` directly, with Claude Code's own OAuth. From 0.5 it starts `fab mcp`, a local stdio bridge that uses mst's login. **Install the new mst first**:

```sh
curl -fsSL https://fab.moltavista.com/install.sh | sh     # mst with `fab mcp`
fab whoami                                                  # who sessions here act as
```

Then update the plugin in Claude Code: `/plugin marketplace update moltavista`, `/plugin update mstep@moltavista`, `/reload-plugins`, and check `/mcp`. The plugin's old OAuth connection is no longer used.

If the plugin updates before mst does, the mstep MCP server fails to start and `/mcp` shows why: "the mst CLI … is too old for it (mst mcp). Update it: curl … | sh". Hooks keep working with the old mst. After updating mst, reconnect with `/mcp`.

## How it fits together

1. At session start, the plugin's `SessionStart` hook (`fab hook session-start`) tells Claude its **mstep client session id** and **whom it acts as** ("You act in mstep as the mstep agent agentEngineer: profile agentEngineer from …/.mst"). It also records which Claude Code session this Claude process runs.
2. The MCP server (`fab mcp`) forwards Claude's MCP calls to `https://fab.moltavista.com/mcp` with the bearer credential of the same identity. It refreshes OAuth tokens and handles long waits (`wait_events`), cancellation and reconnects.
3. When Claude starts on an issue, it calls `session_start` with that id. The issue now shows a live agent session bound to this Claude Code session. The issue is assigned to Claude's identity if nobody had it; an issue assigned to someone else is never taken over, and Claude asks first.
4. Hooks (`fab hook …`, run in the background) forward tool actions ("Running …" while a command runs), the task list, commits/pushes/PR links, permission waits, prompts typed at the terminal, compactions, loaded instruction files, final replies and errors to that session. When the Claude Code session exits, its mstep sessions are ended. The events added in 0.6.0 need an mst with MV-232; older versions ignore them. 0.7.0 adds `PermissionDenied` and the approval hook (below).
5. The monitor (`fab watch`) streams mstep's agent events for the sessions bound to this Claude Code session. It prints one `[mstep] …` line per human message, stop request or decision answer, and per inbox event of the identity. Claude reacts even when idle.

Everything `fab` does in hooks is best effort: hooks never block Claude for more than about 2 s, always succeed, and log to `hook.log` in the resolved CLI config directory (normally `~/.config/fab`, or an existing `~/.config/mst`). The one exception is the opt-in approval hook below. The monitor logs to `watch.log` and the MCP bridge to `mcp.log`.

## Memory reminders (0.7.3, MV-519)

Agents are meant to keep what they learn in mstep's memory (`memory_remember`), and the plugin reminds them at the two points where it gets lost. Each reminder is a sentence or two, given once:

- **Ending a session:** after `session_end`, once per mstep session. In Claude Code a synchronous `PostToolUse` hook that matches only that tool runs `fab hook post-tool-use --remind`. In Codex the synchronous `--deliver` hook adds the reminder.
- **After a compaction:** `SessionStart` runs again (source `compact`) and adds it to the context, once per client session, while the session is bound to an issue.

The `work-on-issue` skill also has the agent read `memory_context` and `memory_search` the area before it starts, and save what it learned before `session_end`. This needs an mst with MV-519. An older mst refuses `--remind`, and Claude Code then logs a hook error on `session_end`.

## Remote approvals (0.7.0, MV-234)

`fab approvals on` (per identity, on this machine; off by default) sends each permission prompt of a session bound to an mstep issue to mstep too.
- **Who answers:** the agent's owner (who signed it in here) or a workspace admin can **allow it once** or **deny it** in the web app, after confirming with a second factor.
- **When nobody answers:** if nobody answers within the wait (default 120 s, `--wait`), or anything fails, the prompt is answered at the terminal as usual. Nothing else ever allows a call.
- **Claude Code** shows its prompt at once, and whichever answer comes first wins. mst learns of an answer given at the terminal from the session's next events (the call running, another call, your next prompt), so until then an answer can still be recorded in mstep for a prompt the terminal already settled.
- **Codex** holds its prompt until mstep answers or the wait ends.

It runs as the synchronous `PermissionRequest` hook `fab hook permission-request --approve`. It needs a profile with an `mst_` token and an mst with MV-234. An older mst refuses the flag, and the prompt is answered at the terminal.

## Several agents on one machine

Hooks, the monitor and the MCP server are all child processes of a Claude Code or Codex instance, so `fab` decides the identity per instance. The first match wins:

1. `FAB_TOKEN` (CI and scripts)
2. `FAB_PROFILE=<name>` (`fab run --as <name>` sets it)
3. a `.fab` or legacy `.mst` file in the working directory or a parent (`fab use <name>` writes it)
4. your `fab login` (the default profile)

```sh
fab login                                          # once: you
fab agent token create agentEngineer               # once per agent: token stored in a profile, never shown
cd ~/code/mstep && claude                          # you
cd ~/code/mstep-wt/agent1 && fab use agentEngineer # pin the worktree (git-ignored .fab and .mst)
claude                                             # there: agentEngineer
fab run --as reviewer -- claude                    # ad hoc, any directory, own memory directory
```

`fab whoami` shows who a session started in the current directory acts as, and why. `fab profiles` lists the identities with their expiry and running instances. `fab profiles rm <name>` revokes and deletes one. Guide: https://fab.moltavista.com/docs/several-agents

## Codex CLI

The same plugin works in OpenAI's [Codex CLI](https://github.com/openai/codex) (0.149 or newer). Codex reads this repository's marketplace and the plugin's `.codex-plugin/plugin.json`, which points at Codex-specific files:

- `codex.mcp.json`: the mstep MCP server. It starts `fab mcp` through a small `sh` lookup ($FAB_BIN, PATH, `~/.local/bin/fab`, then legacy mst locations), because Codex expands no plugin-root variable in a plugin's MCP command. It passes the `FAB_*` variables through `env_vars` (Codex gives stdio servers a minimal environment) and sets `tool_timeout_sec = 120`.
- `hooks/codex-hooks.json`: single-string hook commands running `fab hook <event> --agent codex`.

The skills are shared.

Quickest setup, with the `fab` CLI installed:

```sh
fab codex install          # marketplace + plugin + tool approvals for codex exec; signs you in if needed
codex                      # review and trust the mstep hooks in /hooks
```

Or by hand:

```sh
codex plugin marketplace add https://github.com/moltavista/claude-plugins.git
codex plugin add fab@moltavista
fab login
```

`codex mcp login mstep` is no longer needed: the MCP server uses the CLI's login. To upgrade from 0.4, install the new mst, run `codex plugin marketplace upgrade`, then restart Codex.

How it differs from Claude Code:

- **Live messages**: Codex has no plugin monitors. The SessionStart hook starts `fab watch --agent codex` for the thread. The watcher delivers each `[mstep] …` line with `codex queue` when Codex is idle (that starts a turn), and through a spool while a turn runs: the synchronous `--deliver` hooks hand the spooled lines to Codex (as PostToolUse context, or as a Stop that continues the turn). Each line is delivered exactly once.
- **Hooks must be trusted** once in `/hooks`; `codex exec` needs `--dangerously-bypass-hook-trust` for untrusted hooks.
- **Identities**: `fab use <profile>` pins a directory, so interactive Codex acts as that profile, with live wake-ups. `fab run --as <profile> -- codex …` adds `--no-daemon` for interactive sessions, because Codex's shared background server does not see `FAB_PROFILE`. For headless runs use `fab run --as <profile> -- codex exec …`.
- **Headless (`codex exec`)**: tools that need approval are refused; `fab codex install` approves `session_end` and `decision_cancel` in `config.toml`.
- The plan comes from `update_plan`; permission waits from `PermissionRequest`; Esc from `Interrupt`.

`fab codex status` shows the setup, the identity and running watchers; `fab codex uninstall` removes what `fab codex install` added. Details: https://fab.moltavista.com/docs/codex

## Other servers

The MCP bridge talks to the server of the identity: `fab login --server https://your-mstep` (or `FAB_SERVER`, or `server = "…"` in a `.fab` or legacy `.mst` file) points it elsewhere.

## Troubleshooting

- `fab whoami`: who a session started here acts as, and why. `fab status`: login, workspaces, bound sessions per identity.
- `/mcp` shows the MCP server's error, e.g. "not signed in as profile agentEngineer" or "mst is too old".
- Read `hook.log`, `watch.log` and `mcp.log` in the resolved CLI config directory (`FAB_CONFIG_DIR`, its legacy equivalent, or the default fab/existing mst directory).
- Claude Code: `claude --debug` shows hook runs and MCP server output; `/plugin` → Errors lists load problems.
- Monitors run only in interactive sessions (not with `-p`), and not on Bedrock, Vertex or Foundry.
