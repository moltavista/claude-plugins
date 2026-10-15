// Execute the workflow's actual github-script against a stateful GitHub API fixture.
const fs = require('node:fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const issues = structuredClone(input.issues || []);
const labels = new Set(input.labels || []);
const notices = [];
let next = Math.max(0, ...issues.map(i => i.number)) + 1;
function fail(name) { if (input.fail === name) throw new Error('GitHub API unavailable'); }
const github = { rest: { issues: {
  async listForRepo({ labels: wanted, page, per_page }) {
    fail('list');
    const filtered = issues.filter(i => (i.labels || []).some(l => (l.name || l) === wanted));
    return { data: filtered.slice((page - 1) * per_page, page * per_page) };
  },
  async getLabel({ name }) {
    fail('label');
    if (!labels.has(name)) { const e = new Error('Not Found'); e.status = 404; throw e; }
    return { data: { name } };
  },
  async createLabel({ name }) { fail('createLabel'); labels.add(name); return { data: { name } }; },
  async create(params) {
    fail('create');
    if ((params.labels || []).some(l => !labels.has(l))) throw new Error('unknown label');
    const issue = { ...params, number: next++, state: 'open', user: { login: 'github-actions[bot]', type: 'Bot' } };
    issues.unshift(issue);
    if (input.acceptThenFail === 'create') throw new Error('Response lost after issue creation');
    return { data: issue };
  },
  async update({ issue_number, ...params }) {
    fail('update');
    const issue = issues.find(i => i.number === issue_number);
    if (!issue) throw new Error('unknown issue');
    Object.assign(issue, params); return { data: issue };
  },
} } };
const context = { repo: input.repo || { owner: 'moltavista', repo: 'claude-plugins' }, serverUrl: 'https://github.com', runId: input.runId || 12345, runAttempt: 1 };
const core = { notice: s => notices.push(s), info: s => notices.push(s) };
(async () => {
  let error;
  for (const status of input.results) {
    try {
      const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
      await new AsyncFunction('github', 'context', 'core', 'process', input.script)(github, context, core, { env: { SYNC_RESULT: status } });
    } catch (e) { error = e.message; break; }
  }
  process.stdout.write(JSON.stringify({ issues, labels: [...labels], notices, error }));
})().catch(e => { console.error(e); process.exitCode = 1; });
