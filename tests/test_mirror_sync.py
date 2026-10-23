import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sync-from-forgejo.yml'
MARKER = '<!-- marketplace-sync:begin -->'
END = '<!-- marketplace-sync:end -->'
LABEL = 'marketplace-sync'
TITLE = 'Forgejo marketplace mirror is failing'


def block(key):
    lines = WORKFLOW.read_text().splitlines()
    for index, line in enumerate(lines):
        if line.strip() != key + ': |':
            continue
        indent = len(line) - len(line.lstrip())
        result = []
        for row in lines[index + 1:]:
            if row.strip() and len(row) - len(row.lstrip()) <= indent:
                break
            result.append(row)
        return textwrap.dedent('\n'.join(result))
    raise AssertionError('workflow has no ' + key + ' block for incident reporting')


def owned(number=1, state='open', body=None):
    return {'number': number, 'state': state, 'title': TITLE,
            'body': body or MARKER + '\nOld result\n' + END,
            'labels': [LABEL], 'user': {'login': 'github-actions[bot]', 'type': 'Bot'}}


class MirrorIncidentTests(unittest.TestCase):
    def report(self, results, **fixture):
        request = {'script': block('script'), 'results': results, **fixture}
        result = subprocess.run(['node', str(ROOT / 'tests/mirror_api_harness.cjs')],
                                input=json.dumps(request), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_failure_opens_one_incident_and_repeats_update_it(self):
        result = self.report(['failure', 'failure'])
        self.assertNotIn('error', result)
        self.assertEqual(len(result['issues']), 1)
        issue = result['issues'][0]
        self.assertEqual(issue['state'], 'open')
        self.assertIn('/actions/runs/12345', issue['body'])
        self.assertIn(LABEL, result['labels'])

    def test_a_lost_creation_response_is_recovered_by_the_next_lookup(self):
        ambiguous = self.report(['failure'], acceptThenFail='create')
        self.assertIn('error', ambiguous)
        self.assertEqual(len(ambiguous['issues']), 1)
        retry = self.report(['failure'], issues=ambiguous['issues'],
                            labels=ambiguous['labels'], runId=23456)
        self.assertNotIn('error', retry)
        self.assertEqual(len(retry['issues']), 1)
        self.assertIn('/actions/runs/23456', retry['issues'][0]['body'])

    def test_success_without_an_incident_writes_nothing(self):
        result = self.report(['success'])
        self.assertEqual(result['issues'], [])
        self.assertEqual(result['labels'], [])

    def test_recovery_closes_and_next_failure_reopens_the_same_issue(self):
        result = self.report(['success', 'failure'], issues=[owned()], labels=[LABEL])
        self.assertNotIn('error', result)
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['issues'][0]['number'], 1)
        self.assertEqual(result['issues'][0]['state'], 'open')
        recovery = self.report(['success'], issues=[owned()], labels=[LABEL])
        self.assertEqual(recovery['issues'][0]['state'], 'closed')
        self.assertIn('recovered', recovery['issues'][0]['body'].lower())

    def test_preserves_human_notes_outside_the_managed_section(self):
        note = 'Human investigation: keep this note.'
        result = self.report(['failure'], issues=[owned(body=MARKER + '\nold\n' + END + '\n' + note)], labels=[LABEL])
        self.assertIn(note, result['issues'][0]['body'])

    def test_never_edits_a_human_issue_or_a_pull_request(self):
        human = owned(1)
        human['user'] = {'login': 'maintainer', 'type': 'User'}
        pr = owned(2)
        pr['pull_request'] = {}
        result = self.report(['failure'], issues=[human, pr], labels=[LABEL])
        self.assertEqual(len(result['issues']), 3)
        self.assertEqual(result['issues'][1:], [human, pr])

    def test_notification_api_failure_remains_a_failure(self):
        for method in ['list', 'create', 'update', 'label']:
            with self.subTest(method=method):
                result = self.report(['failure'], issues=[owned()] if method == 'update' else [],
                                     labels=[LABEL] if method == 'create' else [], fail=method)
                self.assertIn('error', result)

    def test_paginated_lookup_reuses_an_existing_incident(self):
        humans = [dict(owned(i), user={'login': 'human', 'type': 'User'}) for i in range(1, 101)]
        result = self.report(['failure'], issues=humans + [owned(101)], labels=[LABEL])
        self.assertNotIn('error', result)
        self.assertEqual(len(result['issues']), 101)
        self.assertIn('/actions/runs/12345', result['issues'][100]['body'])

    def test_bounded_lookup_fails_instead_of_creating_duplicate_incidents(self):
        humans = [dict(owned(i), user={'login': 'human', 'type': 'User'}) for i in range(1, 501)]
        result = self.report(['failure'], issues=humans, labels=[LABEL])
        self.assertIn('error', result)
        self.assertEqual(result['issues'], humans)

    def test_cancellation_and_unexpected_repository_are_refused(self):
        for extra in [{'results': ['cancelled']}, {'results': ['failure'], 'repo': {'owner': 'other', 'repo': 'fork'}}]:
            result = self.report(**extra)
            self.assertIn('error', result)
            self.assertEqual(result['issues'], [])


class MirrorPushTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'GH_', 'GITHUB_', 'FORGEJO_'))}
        self.env.update(HOME=str(self.path / 'home'), GIT_CONFIG_NOSYSTEM='1', GIT_ALLOW_PROTOCOL='file',
                        GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.test',
                        GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.test',
                        FORGEJO_READ_KEY='fixture-not-a-real-key')
        self.github = self.path / 'github.git'
        self.forgejo = self.path / 'forgejo.git'
        for repo in (self.github, self.forgejo):
            self.git(self.path, 'init', '--bare', '--initial-branch=main', str(repo))
        self.source = self.path / 'source'
        self.git(self.path, 'clone', str(self.forgejo), str(self.source))
        (self.source / 'README').write_text('base')
        self.git(self.source, 'add', 'README')
        self.git(self.source, 'commit', '-m', 'base')
        self.git(self.source, 'push', 'origin', 'main')
        self.git(self.source, 'push', str(self.github), 'main')
        self.checkout = self.path / 'checkout'
        self.git(self.path, 'clone', str(self.github), str(self.checkout))
        hosts = self.checkout / '.github'
        hosts.mkdir()
        (hosts / 'forgejo_known_hosts').write_text('fixture host entry\n')
        self.git(self.checkout, 'config', 'url.' + self.forgejo.as_uri() + '.insteadOf',
                 'ssh://git@git.teixos.net/moltavista/claude-plugins.git')

    def git(self, cwd, *args, check=True):
        return subprocess.run(['git', *args], cwd=cwd, env=self.env, text=True,
                              capture_output=True, timeout=10, check=check)

    def advance(self):
        (self.source / 'README').write_text('new marketplace')
        self.git(self.source, 'commit', '-am', 'source advance')
        self.git(self.source, 'push', 'origin', 'main')

    def sync(self):
        return subprocess.run(['bash', '-c', block('run')], cwd=self.checkout,
                              env=self.env, capture_output=True, text=True, timeout=15)

    def test_fast_forwards_the_actual_mirror_and_tags(self):
        self.advance()
        self.git(self.source, 'tag', 'fixture-v1')
        self.git(self.source, 'push', 'origin', '--tags')
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.path, '--git-dir=' + str(self.github), 'rev-parse', 'main').stdout,
                         self.git(self.source, 'rev-parse', 'main').stdout)
        self.assertEqual(self.git(self.path, '--git-dir=' + str(self.github), 'tag').stdout.strip(), 'fixture-v1')

    def test_divergence_is_refused_without_overwriting_github(self):
        self.advance()
        (self.checkout / 'README').write_text('direct GitHub edit')
        self.git(self.checkout, 'commit', '-am', 'direct edit')
        self.git(self.checkout, 'push', 'origin', 'main')
        before = self.git(self.checkout, 'rev-parse', 'main').stdout
        result = self.sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('refusing to force-push', result.stderr)
        self.assertEqual(self.git(self.path, '--git-dir=' + str(self.github), 'rev-parse', 'main').stdout, before)

    def test_missing_key_or_failed_fetch_fail_the_sync(self):
        self.env['FORGEJO_READ_KEY'] = ''
        self.assertNotEqual(self.sync().returncode, 0)
        self.env['FORGEJO_READ_KEY'] = 'fixture'
        self.git(self.checkout, 'config', 'url.' + self.forgejo.as_uri() + '.insteadOf', 'unmatched://')
        self.assertNotEqual(self.sync().returncode, 0)

    def test_a_rejected_tag_push_does_not_report_success(self):
        self.advance()
        self.git(self.source, 'tag', 'fixture-v1')
        self.git(self.source, 'push', 'origin', '--tags')
        hook = self.github / 'hooks/update'
        hook.write_text('#!/bin/sh\ncase "$1" in refs/tags/*) exit 1 ;; esac\n')
        hook.chmod(0o700)
        result = self.sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git(self.path, '--git-dir=' + str(self.github), 'tag').stdout.strip(), '')
