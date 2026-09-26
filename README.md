# Møltavista Claude Code and Codex plugins

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces), also readable by OpenAI's Codex CLI.

```
/plugin marketplace add https://git.teixos.net/moltavista/claude-plugins
# while the moltavista org is private, org members use SSH instead:
# /plugin marketplace add git@git.teixos.net:moltavista/claude-plugins.git
/plugin install mstep@moltavista
```

| Plugin | What it does |
|---|---|
| [mstep](plugins/mstep) | Work [mstep](https://mstep.moltavista.com) issues from Claude Code and Codex: MCP tools, live agent sessions on the issue, decisions for humans, human comments and stop delivered into the running session. |

Codex:

```
codex plugin marketplace add https://git.teixos.net/moltavista/claude-plugins.git
codex plugin add mstep@moltavista
```

(or `mst codex install`, see [plugins/mstep](plugins/mstep#codex-cli)).

Check changes with `claude plugin validate .` and `claude plugin validate plugins/mstep` before pushing, and in Codex with a scratch `CODEX_HOME`: `codex plugin marketplace add <checkout>`, `codex plugin add mstep@moltavista`, `codex mcp list`. Bump the plugin's `version` in both `plugins/mstep/.claude-plugin/plugin.json` and `plugins/mstep/.codex-plugin/plugin.json` so installed copies update. mst embeds the skills and `hooks/codex-hooks.json` for `mst codex install --direct`: after changing them, copy them to mstep's `internal/mst/codexassets` (`just codex-plugin-check` there compares).
