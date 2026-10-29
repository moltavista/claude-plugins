# moltaget plugin

Connects Claude Code to [moltaget](https://mget.moltavista.com), Møltavista's
web-scraping service for agents, and teaches Claude when to use it.

- **MCP server** `moltaget` → `https://mget.moltavista.com/mcp` (remote,
  Streamable HTTP). Tools: `scrape`, `map`, `search`, `crawl`,
  `batch_scrape`, `extract`, `get_job`, `cancel_job`, `search_corpus`,
  `account`.
- **Skill** `moltaget`: which tool to reach for, job polling, credit costs,
  and the errors worth handling.

## Install

```
/plugin marketplace add https://github.com/moltavista/claude-plugins
/plugin install moltaget@moltavista
```

or, in one step (Claude Code 2.1.275 or later):

```
/plugin install moltaget --marketplace https://github.com/moltavista/claude-plugins
```

## Sign in

Run `/mcp`, select **moltaget**, choose **Authenticate**. Your browser opens
moltaget: sign in with Google, pick the team the agent may spend credits
for, approve. Claude Code receives a moltaget client token by itself — there
is nothing to copy. It shows up on the
[Tokens page](https://mget.moltavista.com/#/tokens) as
`MCP · Claude Code · <date>`; revoke it there to disconnect.

No browser available (CI, a remote box)? Mint a token on the Tokens page and
add the server with a header instead of installing the plugin's config:

```
claude mcp add --transport http moltaget https://mget.moltavista.com/mcp \
  --header "Authorization: Bearer mt-…"
```

## Details

- User docs: <https://mget.moltavista.com/docs/mcp>
- Design (OAuth flow, tools as a translation of the REST API): `docs/mcp.md`
  in the moltaget repository.
