"""Managed bindings survive the minimal environment of the stdio client."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINDINGS = ['FAB_PROFILE', 'FAB_SERVER', 'FAB_CONFIG_DIR', 'FAB_MANAGED_FOLDER',
            'FAB_MANAGED_HARNESS', 'FAB_MANAGED_GENERATION', 'FAB_CODEX_SOCKET']


class ManagedCodexEnvironmentTests(unittest.TestCase):
    def test_bridge_receives_managed_bindings_without_ambient_credentials(self):
        server = json.loads((ROOT / 'plugins/mstep/codex.mcp.json').read_text())['mcpServers']['mstep']
        with tempfile.TemporaryDirectory(prefix='managed-codex-env-') as temp:
            binary = Path(temp) / 'mst'
            binary.write_text('#!/bin/sh\nif [ "$2" = --help ]; then exit 0; fi\n' +
                              '\n'.join('printf "%s\\n" "${' + key + '-missing}"' for key in BINDINGS) + '\n')
            binary.chmod(0o700)
            parent = {key: 'fixture-' + key for key in BINDINGS}
            parent['MST_BIN'] = str(binary)
            # Do not select a real preferred fab binary from the developer's PATH.
            env = {'HOME': temp, 'PATH': temp + ':/usr/bin:/bin'}
            env.update({key: value for key, value in parent.items() if key in server['env_vars']})
            result = subprocess.run([server['command'], *server['args']], env=env,
                                    input='', capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [parent[key] for key in BINDINGS])
            self.assertEqual(len(server['env_vars']), len(set(server['env_vars'])))
