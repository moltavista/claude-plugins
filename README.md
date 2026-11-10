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

Use the **moltaget** plugin to scrape, map, search and crawl the web through [moltaget](https://mget.moltavista.com)'s MCP server. Sign in with Google from `/mcp`; no token to copy.

```
/plugin install moltaget@moltavista
```

See [the moltaget plugin guide](plugins/moltaget).

For fabbrica, install **one** entry. `mstep@moltavista` is **deprecated**: existing installs keep working for one transition cycle, but install `fab@moltavista` and remove the alias; do not enable both, which would duplicate hooks and watchers. From 0.9 the MCP server is named `fabbrica` and live events start with `[fabbrica]`; `[mstep]` lines from older servers are handled the same, under the same trust rules. 0.9 needs a fab CLI that reads the new names: update the CLI first (see [Upgrading to 0.9](plugins/fab#upgrading-to-09-the-fabbrica-names)). Switching entries does not migrate credentials, edit running agents or restart their watchers.

See [the fab plugin guide](plugins/fab) for identities, hook privacy, approvals, Codex and troubleshooting. The [compatibility guide](plugins/mstep) covers existing installs.

Maintainers: run `GO111MODULE=off go test ./tests` and the existing `python3 -m unittest discover -s tests`, `claude plugin validate .`, and validate both plugin directories with a scratch home. New tooling uses Go or shell. Test marketplace installation and MCP listing with a scratch `CODEX_HOME`. Never update a person's live harness during validation. Keep both entries' bridge, hooks, monitors and skills identical and bump their Claude and Codex manifest versions together. The Go release-contract test pins the current version; the legacy transition suite checks manifest parity. The final mstep bundle PR updates its embedded Codex assets and direct configuration after this plugin transition ships.

## One-time secret delivery compatibility

Version 0.8.7 adds a synchronous native prehook for direct `decision_secret_consume` calls, including a renamed MCP server. It requires the matching reviewed fab CLI release and its native-execution verification. Older CLIs or unproved bridge origins cannot deliver the answer. Codex additionally needs native request-thread metadata (verified in 0.162.1); wrappers without native proof are unsupported.

Before forwarding a supported consume, the CLI durably pauses automatic content reporting for that native session. Tool results, automatic responses, live/terminal capture and remote approval summaries stay paused across session end/resume and CLI restart. Incoming steering and lifecycle metadata continue. The marker contains references, never the secret. The receiving model, provider and native transcript still receive the explicitly authorised value; this does not protect against that recipient retaining or disclosing it. Secret purposes remain off until separately activated.

This PR does not install hooks in existing homes or trust changed definitions. Review the changed hooks in the host's normal trust UI after installing the matching released CLI and plugin.

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
