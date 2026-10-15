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

## Maintainers: edit Forgejo, not the GitHub mirror

[Forgejo](https://git.teixos.net/moltavista/claude-plugins) is the source of truth.
Send changes and pull requests there. GitHub is the installation mirror; do not
commit, merge a pull request or edit a file directly on GitHub. A direct GitHub
commit makes the branches diverge and blocks the next fast-forward sync.

The [marketplace sync workflow](https://github.com/moltavista/claude-plugins/actions/workflows/sync-from-forgejo.yml)
runs every 30 minutes and can also be dispatched manually. A failed sync opens or
reopens one [marketplace-sync incident](https://github.com/moltavista/claude-plugins/issues?q=is%3Aissue+label%3Amarketplace-sync),
updates its latest run link on repeated failures, and closes it after recovery.
The failed run stays red even if incident reporting also fails. Reporting cannot
notice when GitHub stops scheduling the workflow; an independent cluster watch
is tracked separately in [MV-765](https://fab.moltavista.com/moltavista/issue/MV-765).

When an incident opens:

1. Follow its run link. Check whether checkout, credentials, fetching, divergence
   or a main/tag push failed; never copy private keys into an issue or log.
2. Fix the source or credentials through the reviewed path. For divergence,
   preserve the GitHub-only commit by merging it into Forgejo through a pull
   request, as in [MV-763](https://fab.moltavista.com/moltavista/issue/MV-763).
   The workflow deliberately refuses to force-push.
3. Dispatch the sync after the fix and check that it succeeds, the incident
   records recovery, and the GitHub marketplace contains the expected plugin.

Changes to the sync workflow itself may require a maintainer to fast-forward the
same reviewed Forgejo commit to GitHub with a credential allowed to update
workflow files. Do not create another GitHub-only commit to install that change.
