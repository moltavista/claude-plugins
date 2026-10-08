# Møltavista Claude Code and Codex plugins

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces), also readable by OpenAI's Codex CLI.

The mstep plugin needs the `mst` CLI (its MCP server runs through `mst mcp`): `curl -fsSL https://fab.moltavista.com/install.sh | sh && mst login`, then `mst claude install`, or in Claude Code. Verified standalone binaries are also available from the [public mst releases](https://github.com/moltavista/mst/releases/latest).

```
/plugin marketplace add https://github.com/moltavista/claude-plugins
/plugin install mstep@moltavista
```

| Plugin | What it does |
|---|---|
| [mstep](plugins/mstep) | Work [mstep](https://fab.moltavista.com) issues from Claude Code and Codex: MCP tools, live agent sessions on the issue, decisions for humans, human comments and stop delivered into the running session. |

Codex:

```
codex plugin marketplace add https://github.com/moltavista/claude-plugins.git
codex plugin add mstep@moltavista
```

(or `mst codex install`, see [plugins/mstep](plugins/mstep#codex-cli)). Several Claude Code / Codex sessions acting as different agents on one machine: [plugins/mstep](plugins/mstep#several-agents-on-one-machine).


Check changes with `claude plugin validate .` and `claude plugin validate plugins/mstep` before pushing, and in Codex with a scratch `CODEX_HOME`: `codex plugin marketplace add <checkout>`, `codex plugin add mstep@moltavista`, `codex mcp list`. Bump the plugin's `version` in both `plugins/mstep/.claude-plugin/plugin.json` and `plugins/mstep/.codex-plugin/plugin.json` so installed copies update. mst embeds the skills, `hooks/codex-hooks.json` and `codex.mcp.json` (`mst codex install --direct`, and the list of variables `mst mcp` needs): after changing them, copy them to mstep's `internal/mst/codexassets` (`just codex-plugin-check` there compares).
