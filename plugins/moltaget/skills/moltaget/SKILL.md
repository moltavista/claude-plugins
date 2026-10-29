---
name: moltaget
description: Use when you need the content of a web page or site - read a URL as clean markdown, list a site's pages, search the web, crawl or batch-scrape many pages, extract structured JSON, or search pages the team already crawled - through the moltaget MCP tools (mcp__moltaget__*). Covers connecting/signing in, which tool to pick, job polling, credit costs and the errors worth handling.
---

# moltaget

moltaget (mget) turns URLs into agent-ready content. This plugin connects
Claude Code to its MCP server at `https://mget.moltavista.com/mcp`; the tools
appear as `mcp__moltaget__<tool>`. Prefer them to WebFetch or hand-written
HTTP calls whenever a page's content matters: they render JavaScript when a
page needs it, strip boilerplate, and work through the team's stored site
logins and egress.

## Connecting

The first call answers "needs authentication". Tell the user to run `/mcp`,
pick **moltaget** and choose **Authenticate**: a browser opens, they sign in
with Google (moltavista account), choose the team whose credits the agent may
spend, and approve. Claude Code receives the token by itself — never ask the
user to paste a token into the conversation. The token is listed on
`https://mget.moltavista.com/#/tokens` as `MCP · Claude Code · <date>`;
revoking it there disconnects, and the next call asks to authenticate again.

Headless (CI, no browser): a human mints a token on the Tokens page and
configures the server with
`claude mcp add --transport http moltaget https://mget.moltavista.com/mcp --header "Authorization: Bearer mt-…"`.

## Pick the cheapest tool that answers the question

| You have | You want | Tool |
|---|---|---|
| One URL | its text | `scrape` (markdown by default) |
| One URL | specific fields | `scrape` with `formats: [{"type":"json","prompt":"…","schema":{…}}]` |
| A site | which pages exist | `map` (1 credit flat, no page fetches) |
| A question | pages about it | `search` (add `scrapeOptions` only if you need their text) |
| Pages the team crawled before | matches | `search_corpus` (no new fetch) |
| A site section | every page's text | `map` first, then `crawl` with `includePaths` and a `limit` |
| A known URL list | all of them | `batch_scrape` |
| Many pages | one merged JSON object | `extract` |
| — | balance, team, who am I | `account` |

Arguments are the moltaget REST API's (Firecrawl-compatible, camelCase):
`formats`, `onlyMainContent`, `includeTags`, `excludeTags`, `waitFor`,
`timeout`, `headers`, `actions`, `location`, `maxAge`, `fetcher`
(`auto` | `http` | `browser`), `proxy` (`{"name": …}` or `{"country": …}` to
pick a saved egress). Two MCP-only arguments: `maxChars` caps the page text
in one result (default 100000 — raise it only when you need the rest), and
`get_job` takes `cursor`.

## Jobs (crawl, batch_scrape, extract)

They return an `id` at once. Call `get_job` with it:

- Wait between polls — a few seconds at first, 10–15 s for a long job (look
  at `total`/`completed`). Do other work in between when you can.
- Stop at `completed`, `failed` or `cancelled`.
- `paused` is not terminal. With `reason: insufficient_credits` it resumes
  by itself when credits arrive (or fails at `pausedUntil`); a job paused
  deliberately in the UI never resumes on its own — say so and stop polling.
- Results come one page at a time: pass `next_cursor` back as `cursor` until
  it is absent. Each page's text is cut to `maxChars` in total.
- `cancel_job` stops a job you no longer need; fetched pages stay billed.

## Credits

| What | Cost |
|---|---|
| Page over HTTP | 1 |
| Page rendered in a browser | 5 |
| `screenshot`, `json`/`summary`, OCR of a PDF/image | +1 each |
| Cache hit | 50% (own team's entry) or 80% (another team's anonymous fetch) |
| Failed or refused page | 0 |
| `map` | 1 per call |
| `search` | 2 per 10 results |
| `search_corpus` | 1 per 10 results |

So: leave `fetcher` on `auto` (it escalates to the browser only when the page
needs it), don't pass `maxAge: 0` unless you need fresh content, always give
`crawl` a `limit`, and look in `search_corpus` before re-crawling a site the
team already has. Before a large crawl, say how many pages it may fetch.

## Errors worth handling

Tool errors arrive as the tool result's text:

| Text starts with / contains | Meaning | Do |
|---|---|---|
| `insufficient_credits` | The team's balance is spent | Stop and tell the user; retrying cannot help |
| `aup_required` | The connected user has not accepted the current acceptable use policy | Ask them to open moltaget and accept it, then retry |
| `rate_limited` / `concurrency_limited` … `(retry after Ns)` | Throttled | Wait the stated seconds, then retry once |
| `denylisted` / `team_suspended` | Policy refusal | Do not retry that target |
| `invalid arguments: field "…"` | A wrong argument shape | Fix the argument |
| a timeout with `diagnostics` | The browser could not finish the page | Retry with a larger `timeout` or `waitFor`, or try `fetcher: "http"` |

A successful `scrape` can still be an error page: check `statusCode` in the
header lines above the markdown. `json` and `summary` formats and `extract`
need a model backend configured for the team; a `failed_precondition` naming
that is for the user to fix, not to retry.

More: `https://mget.moltavista.com/docs/mcp` and, for the REST API behind the
tools, `https://mget.moltavista.com/skill/mget/SKILL.md`.
