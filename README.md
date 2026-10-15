# Møltavista Claude Code and Codex plugins

Use the **fab** plugin to work [fabbrica](https://fab.moltavista.com) issues: MCP tools, live agent sessions, human decisions and steering.

The plugin prefers the `fab` CLI and accepts the compatible `mst` CLI during the transition. Install the CLI from `https://fab.moltavista.com/install.sh` and sign in with `fab login` (or `mst login` if the installer still supplies `mst`). Existing profiles and directory pins remain usable.

Claude Code:

```
/plugin marketplace add https://github.com/moltavista/claude-plugins
/plugin install fab@moltavista
```

Codex:

```
codex plugin marketplace add https://github.com/moltavista/claude-plugins.git
codex plugin add fab@moltavista
```

Install **one** entry. Existing `mstep@moltavista` installs keep working as a compatibility alias for one transition cycle; do not enable it alongside `fab@moltavista`, which would duplicate hooks and watchers. The MCP server remains named `mstep`, and live events retain the `[mstep]` prefix during this cycle. Switching entries does not migrate credentials, edit running agents or restart their watchers.

See [the fab plugin guide](plugins/fab) for identities, hook privacy, approvals, Codex and troubleshooting. The [compatibility guide](plugins/mstep) covers existing installs.

Maintainers: run `python3 -m unittest discover -s tests`, `claude plugin validate .`, and validate both plugin directories with a scratch home. Test marketplace installation and MCP listing with a scratch `CODEX_HOME`. Never update a person's live harness during validation. Keep both entries' bridge, hooks, monitors and skills identical and bump their Claude and Codex manifest versions together. The final mstep bundle PR updates its embedded Codex assets and direct configuration after this plugin transition ships.
