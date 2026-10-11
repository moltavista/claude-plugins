import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(os.environ.get('FAB_TEST_TMP') or tempfile.gettempdir()) / 'fab-plugin-tests'
CACHE.mkdir(parents=True, exist_ok=True)


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(dir=CACHE)
        self.addCleanup(self.scratch.cleanup)
        self.home = Path(self.scratch.name)
        self.bin = self.home / 'bin'
        self.bin.mkdir()
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(('MST_', 'FAB_', 'CLAUDE_', 'CODEX_', 'XDG_'))}
        self.env.update(HOME=str(self.home), PATH=f'{self.bin}:/usr/bin:/bin',
                        TMPDIR=str(self.home))

    def binary(self, name, label, old=False):
        p = self.bin / name
        p.write_text('#!/bin/sh\n' +
                     ('[ "$1 $2" != "mcp --help" ] || exit 1\n' if old else '') +
                     f'printf "{label}:%s:%s:%s\\n" "$*" "${{MST_PROFILE:-}}" "${{FAB_PROFILE:-}}"\n')
        p.chmod(0o700)
        return str(p)

    def launchers(self):
        yield ['/bin/sh', str(ROOT / 'plugins/mstep/scripts/fab-run')]
        cfg = json.loads((ROOT / 'plugins/mstep/codex.mcp.json').read_text())
        server = next(iter(cfg['mcpServers'].values()))
        yield [server['command'], *server['args']]

    def run_launcher(self, cmd, **extra):
        env = self.env | extra
        return subprocess.run(cmd, env=env, input='', text=True,
                              capture_output=True, timeout=5)

    def test_both_launchers_prefer_fab_and_preserve_legacy_profile(self):
        self.binary('fab', 'fab')
        self.binary('mst', 'mst')
        for cmd in self.launchers():
            with self.subTest(cmd=cmd):
                r = self.run_launcher(cmd + ([] if '-c' in cmd else ['mcp']), MST_PROFILE='Alice')
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(r.stdout.startswith('fab:mcp'), r.stdout)

    def test_both_launchers_fallback_and_translate_preferred_profile(self):
        self.binary('mst', 'mst')
        for cmd in self.launchers():
            with self.subTest(cmd=cmd):
                r = self.run_launcher(cmd + ([] if '-c' in cmd else ['mcp']),
                                      MST_PROFILE='Other', FAB_PROFILE='Alice')
                self.assertIn('mst:mcp:Alice:Alice', r.stdout)

    def test_explicit_fab_binary_overrides_explicit_legacy_binary(self):
        fab = self.binary('preferred', 'fab')
        mst = self.binary('legacy', 'mst')
        for cmd in self.launchers():
            r = self.run_launcher(cmd + ([] if '-c' in cmd else ['mcp']), FAB_BIN=fab, MST_BIN=mst)
            self.assertTrue(r.stdout.startswith('fab:mcp'), r.stdout)

    def test_empty_preferred_profile_does_not_use_legacy_profile(self):
        self.binary('mst', 'mst')
        for cmd in self.launchers():
            r = self.run_launcher(cmd + ([] if '-c' in cmd else ['mcp']), FAB_PROFILE='', MST_PROFILE='Other')
            self.assertIn('mst:mcp::', r.stdout)

    def test_old_fab_falls_back_to_mst_bridge(self):
        self.binary('fab', 'old', old=True)
        self.binary('mst', 'mst')
        for cmd in self.launchers():
            r = self.run_launcher(cmd + ([] if '-c' in cmd else ['mcp']))
            self.assertTrue(r.stdout.startswith('mst:mcp'), r.stdout)

    def test_hook_passes_arguments_and_stdin_without_restarting_watchers(self):
        p = self.bin / 'fab'
        p.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\ncat\n')
        p.chmod(0o700)
        wrapper = ROOT / 'plugins/mstep/scripts/fab-run'
        r = subprocess.run(['/bin/sh', str(wrapper), 'hook', 'post-tool-use', '--agent', 'codex'],
                           env=self.env, input='{"event":"fixture"}\n', text=True, capture_output=True, timeout=5)
        self.assertEqual(r.stdout, 'hook\npost-tool-use\n--agent\ncodex\n{"event":"fixture"}\n')

    def test_missing_bridge_returns_valid_error_with_same_request_id(self):
        for cmd in self.launchers():
            for request in [
                '{"jsonrpc":"2.0","id":7,"method":"initialize"}',
                '{"method":"initialize","jsonrpc":"2.0","id":"client-a"}',
            ]:
                r = subprocess.run(cmd + ([] if '-c' in cmd else ['mcp']), env=self.env,
                                   input=request + '\n', text=True, capture_output=True, timeout=5)
                answer = json.loads(r.stdout)
                self.assertEqual(answer['id'], json.loads(request)['id'])
                self.assertEqual(answer['error']['code'], -32000)
                self.assertIn('fab', answer['error']['message'])
                self.assertNotIn(str(self.home), answer['error']['message'])

    def test_missing_hooks_are_quiet_and_hint_once(self):
        wrapper = ROOT / 'plugins/mstep/scripts/fab-run'
        for args in [['hook', 'post-tool-use'], ['hook', 'stop']]:
            r = self.run_launcher(['/bin/sh', str(wrapper), *args])
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, '', ''))
        cmd = ['/bin/sh', str(wrapper), 'hook', 'session-start']
        self.assertIn('fabbrica', self.run_launcher(cmd).stdout)
        self.assertEqual(self.run_launcher(cmd).stdout, '')

    def test_cached_wrapper_remains_compatible(self):
        self.binary('mst', 'mst')
        r = self.run_launcher(['/bin/sh', str(ROOT / 'plugins/mstep/scripts/mst-run'),
                               'watch', '--state-dir', 'path with spaces'])
        self.assertIn('mst:watch --state-dir path with spaces', r.stdout)

    def test_codex_inline_helper_matches_shared_helper(self):
        shared = (ROOT / 'plugins/mstep/scripts/fab-run').read_text().replace('#!/bin/sh\n', '', 1)
        cfg = json.loads((ROOT / 'plugins/mstep/codex.mcp.json').read_text())
        server = next(iter(cfg['mcpServers'].values()))
        self.assertEqual(server['args'][1], shared + '\n')
        self.assertEqual(server['args'][2:], ['fab-mcp', 'mcp'])

    def test_codex_passes_both_environment_families(self):
        cfg = json.loads((ROOT / 'plugins/mstep/codex.mcp.json').read_text())
        names = next(iter(cfg['mcpServers'].values()))['env_vars']
        for name in ['PROFILE', 'TOKEN', 'SERVER', 'CONFIG_DIR', 'CREDENTIAL_STORE', 'BIN', 'DEBUG', 'REPORT_PROMPTS', 'UPLOAD_IMAGES', 'WATCH_INBOX', 'WATCH_INBOX_KINDS', 'AUTO_UPDATE', 'CODEX_BIN', 'CODEX_LIVE', 'COMPACT_INJECT', 'HELPER_REFRESH', 'KEYCHAIN', 'MCP_RESUME', 'TERM']:
            self.assertIn('FAB_' + name, names)
            self.assertIn('MST_' + name, names)

    def test_codex_preserves_managed_lifecycle_selectors(self):
        cfg = json.loads((ROOT / 'plugins/mstep/codex.mcp.json').read_text())
        names = next(iter(cfg['mcpServers'].values()))['env_vars']
        for name in ['FAB_PROFILE', 'FAB_SERVER', 'FAB_CONFIG_DIR', 'FAB_MANAGED_FOLDER',
                     'FAB_MANAGED_HARNESS', 'FAB_MANAGED_GENERATION', 'FAB_CODEX_SOCKET']:
            self.assertIn(name, names)

    def test_marketplace_offers_fab_and_one_cycle_mstep_alias(self):
        market = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        names = {p['name']: p for p in market['plugins']}
        self.assertEqual(set(names), {'fab', 'mstep'})
        for name in names:
            path = ROOT / names[name]['source']
            claude = json.loads((path / '.claude-plugin/plugin.json').read_text())
            codex = json.loads((path / '.codex-plugin/plugin.json').read_text())
            self.assertEqual(claude['name'], name)
            self.assertEqual(codex['name'], name)
            self.assertEqual(claude['version'], codex['version'])
            self.assertEqual(claude['version'], '0.8.3')
            self.assertEqual(set(json.loads((path / 'codex.mcp.json').read_text())['mcpServers']), {'mstep'})
            for relative in ['codex.mcp.json', '.mcp.json', 'hooks/hooks.json',
                             'hooks/codex-hooks.json', 'monitors/monitors.json', 'scripts/fab-run']:
                self.assertEqual((path / relative).read_bytes(),
                                 (ROOT / 'plugins/mstep' / relative).read_bytes())

    def test_both_entries_retain_synchronous_memory_reminder(self):
        for name in ['fab', 'mstep']:
            path = ROOT / 'plugins' / name
            hooks = json.loads((path / 'hooks/hooks.json').read_text())['hooks']['PostToolUse']
            reminders = [(group, hook) for group in hooks for hook in group['hooks']
                         if '--remind' in hook.get('args', [])]
            self.assertEqual(len(reminders), 1)
            group, hook = reminders[0]
            self.assertEqual(group['matcher'], 'mcp__.*mstep.*__session_end')
            self.assertFalse(hook.get('async', False))
            self.assertTrue(hook['command'].endswith('/scripts/fab-run'))
            skill = (path / 'skills/work-on-issue/SKILL.md').read_text()
            self.assertIn('memory_search', skill)
            self.assertIn('memory_remember', skill)


if __name__ == '__main__':
    unittest.main()
