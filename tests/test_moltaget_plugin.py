import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/moltaget'


class MoltagetPluginTest(unittest.TestCase):
    def test_marketplace_entry_points_at_the_plugin(self):
        market = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        entry = next(p for p in market['plugins'] if p['name'] == 'moltaget')
        self.assertEqual((ROOT / entry['source']).resolve(), PLUGIN)
        manifest = json.loads((PLUGIN / '.claude-plugin/plugin.json').read_text())
        self.assertEqual(manifest['name'], 'moltaget')
        self.assertRegex(manifest['version'], r'^\d+\.\d+\.\d+$')

    def test_mcp_server_is_the_remote_endpoint_with_no_secret(self):
        servers = json.loads((PLUGIN / '.mcp.json').read_text())['mcpServers']
        self.assertEqual(set(servers), {'moltaget'})
        server = servers['moltaget']
        self.assertEqual(server['type'], 'http')
        self.assertEqual(server['url'], 'https://mget.moltavista.com/mcp')
        # Sign-in is OAuth driven by the client: the plugin must never carry
        # a token or an Authorization header.
        self.assertNotIn('headers', server)
        self.assertNotIn('mt-', json.dumps(servers))

    def test_skill_frontmatter(self):
        text = (PLUGIN / 'skills/moltaget/SKILL.md').read_text()
        m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
        self.assertIsNotNone(m)
        front = dict(line.split(': ', 1) for line in m.group(1).splitlines())
        self.assertEqual(front['name'], 'moltaget')
        self.assertTrue(front['description'].startswith('Use when'))
        self.assertLessEqual(len(front['description']), 1024)
        for tool in ['scrape', 'map', 'search', 'crawl', 'batch_scrape', 'extract',
                     'get_job', 'cancel_job', 'search_corpus', 'account']:
            self.assertIn(f'`{tool}`', text)


if __name__ == '__main__':
    unittest.main()
