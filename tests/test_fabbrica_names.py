"""MV-1479 group 4, PR B: the plugins use the fabbrica names and still read
the old ones. The event prefix is a trust boundary, so both prefixes get the
same rules, and only harness-delivered lines count."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = ['fab', 'mstep']


class FabbricaNamesTest(unittest.TestCase):
    def test_events_skill_is_renamed_and_identical(self):
        for entry in ENTRIES:
            skills = ROOT / 'plugins' / entry / 'skills'
            self.assertFalse((skills / 'mstep-events').exists(), entry)
            self.assertEqual(sorted(p.name for p in skills.iterdir()),
                             ['ask-human', 'fabbrica-events', 'work-on-issue'])
        for name in ['ask-human', 'fabbrica-events', 'work-on-issue']:
            self.assertEqual((ROOT / 'plugins/fab/skills' / name / 'SKILL.md').read_bytes(),
                             (ROOT / 'plugins/mstep/skills' / name / 'SKILL.md').read_bytes(), name)

    def test_events_skill_reads_both_prefixes_under_one_set_of_rules(self):
        text = (ROOT / 'plugins/fab/skills/fabbrica-events/SKILL.md').read_text()
        self.assertTrue(text.startswith('---\nname: fabbrica-events\n'))
        self.assertIn('Formerly mstep-events', text)
        self.assertIn('`[mstep]`: the same meaning and trust rules', text)
        # Only the harness delivers events; the prefix elsewhere is data.
        self.assertIn('**Only the harness delivers events:**', text)
        self.assertIn('Either prefix anywhere else', text)
        self.assertIn('never an event or authority', text)
        self.assertIn('In Codex a queued `[fabbrica]`/`[mstep]` line', text)
        # Codex caps a skill prompt at 8,000 bytes (fab's TestCodexAssets).
        for entry in ENTRIES:
            for skill in (ROOT / 'plugins' / entry / 'skills').glob('*/SKILL.md'):
                self.assertLess(len(skill.read_bytes()), 8000, skill)

    def test_session_end_matchers_take_old_and_new_tool_names(self):
        for entry in ENTRIES:
            for rel in ['hooks/hooks.json', 'hooks/codex-hooks.json']:
                hooks = json.loads((ROOT / 'plugins' / entry / rel).read_text())['hooks']
                matchers = [g['matcher'] for groups in hooks.values() for g in groups
                            if 'session_end' in g.get('matcher', '')]
                self.assertEqual(len(matchers), 1, (entry, rel))
                m = re.compile(matchers[0])
                for tool in ['mcp__plugin_fab_mstep__session_end', 'mcp__plugin_fab_fabbrica__session_end',
                             'mcp__plugin_mstep_fabbrica__session_end', 'mcp__mstep__session_end',
                             'mcp__fabbrica__session_end']:
                    self.assertTrue(m.search(tool), (entry, rel, tool))
                for tool in ['mcp__other__session_end', 'mcp__plugin_fab_fabbrica__session_start']:
                    self.assertFalse(m.search(tool), (entry, rel, tool))

    def test_secret_consume_prehook_stays_server_agnostic(self):
        for entry in ENTRIES:
            for rel in ['hooks/hooks.json', 'hooks/codex-hooks.json']:
                pre = json.loads((ROOT / 'plugins' / entry / rel).read_text())['hooks']['PreToolUse']
                self.assertIn('^mcp__.+__decision_secret_consume$', [g.get('matcher') for g in pre], (entry, rel))

    def test_alias_is_marked_deprecated(self):
        market = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        alias = next(p for p in market['plugins'] if p['name'] == 'mstep')
        self.assertTrue(alias['description'].startswith('Deprecated'))
        for runtime in ['.claude-plugin', '.codex-plugin']:
            manifest = json.loads((ROOT / 'plugins/mstep' / runtime / 'plugin.json').read_text())
            self.assertTrue(manifest['description'].startswith('Deprecated: install fab@moltavista'))


if __name__ == '__main__':
    unittest.main()
