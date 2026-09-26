# Møltavista Claude Code plugins

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces).

```
/plugin marketplace add https://git.teixos.net/moltavista/claude-plugins
/plugin install mstep@moltavista
```

| Plugin | What it does |
|---|---|
| [mstep](plugins/mstep) | Work [mstep](https://mstep.moltavista.com) issues from Claude Code: MCP tools, live agent sessions on the issue, decisions for humans, human comments and stop delivered into the running session. |

Check changes with `claude plugin validate .` and `claude plugin validate plugins/mstep` before pushing; bump the plugin's `version` in `plugins/mstep/.claude-plugin/plugin.json` so installed copies update.
