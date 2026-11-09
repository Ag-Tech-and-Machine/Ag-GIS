"""Developer-only disk/model handoff composition, NOT native or product login."""
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from auth_flow_model import RefreshFlow
from auth_refresh_fence import RefreshFence
from auth_refresh_readback_test import pair
import auth_refresh_readback as gate

BASE = Path.home() / 'AppData/Local/hermes/cache/scratch'


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aggis-handoff-', dir=BASE)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'fence.sqlite3'
        RefreshFence.create(self.path, 'fixture-slot', revision='fixture-old', expires_at=200)
        self.fence = RefreshFence(self.path, 'fixture-slot')
        self.attempt = self.fence.begin_bound('fixture-old', expires_at=200, now=100)
        self.assertIsNotNone(self.attempt)
        assert self.attempt is not None
        self.clock = [0]
        self.flow = RefreshFlow(lambda: self.clock[0], pair('old'))
        request = self.flow.start('SYNTHETIC-CLIENT')
        assert request is not None
        self.key = request.key
        self.assertTrue(self.flow.receive(self.key, 200, pair('new')))
        self.record = dict(slot='fixture-slot', attempt=self.attempt, old_revision='fixture-old',
                           revision='fixture-new', expires_at=300, pair=pair('new'))

    def handoff(self, readback=None, fence=None):
        function = getattr(gate, 'acknowledge_committed_fixture_readback', None)
        self.assertTrue(callable(function), 'Missing commit-before-model-ack fixture gate')
        assert callable(function)
        return function(self.flow, self.key, fence=fence or self.fence, write_ok=True,
                        revision='fixture-new', expires_at=300, old_expires_at=200, now=100,
                        binding={name: self.record[name] for name in ('slot', 'attempt', 'old_revision')},
                        readback=readback or (lambda: self.record))

    def disk(self):
        with closing(sqlite3.connect(self.path)) as conn:
            return (conn.execute('SELECT state FROM refresh_fence').fetchone()[0],
                    conn.execute('SELECT * FROM refresh_replacement').fetchall())

    def test_exact_receipt_commits_before_model_success(self):
        saved = self.flow.saved
        observations = []
        def observe(key, success):
            if success is True:
                state, rows = self.disk()
                self.assertEqual(state, 'reconciled')
                self.assertEqual(rows, [('fixture-slot', self.attempt, 'fixture-old', 200,
                                         'fixture-new', 300)])
                observations.append(True)
            return saved(key, success)
        self.flow.saved = observe
        self.assertTrue(self.handoff())
        self.assertEqual(observations, [True])
        self.assertEqual(self.flow.take_tokens(), pair('new'))
        self.assertIsNone(self.flow.take_tokens())
        reads = []
        before = self.path.read_bytes()
        self.assertFalse(self.handoff(readback=lambda: reads.append(True)))
        self.assertEqual(reads, [])
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_old_expiry_refuses_before_protected_read(self):
        function = getattr(gate, 'acknowledge_committed_fixture_readback')
        reads = []
        self.assertFalse(function(
            self.flow, self.key, fence=self.fence, write_ok=True,
            revision='fixture-new', expires_at=300, old_expires_at=True, now=100,
            binding={name: self.record[name] for name in ('slot', 'attempt', 'old_revision')},
            readback=lambda: reads.append(True) or self.record))
        self.assertEqual(reads, [], 'Invalid old expiry must skip protected read')
        self.assertIsNone(self.flow.take_tokens())
        self.assertEqual(self.disk(), ('uncertain', []))

    def test_real_busy_commit_never_acknowledges_and_rolls_back(self):
        before = self.path.read_bytes()
        with closing(sqlite3.connect(self.path, timeout=0)) as reader:
            reader.execute('BEGIN')
            reader.execute('SELECT * FROM refresh_fence').fetchall()
            self.assertFalse(self.handoff())
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.disk(), ('uncertain', []))
        self.assertIsNone(self.flow.take_tokens())
        self.assertEqual(self.flow.state, 'reauth_required')

    def test_real_trigger_abort_never_acknowledges(self):
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute("CREATE TRIGGER refuse_terminal BEFORE UPDATE ON refresh_fence "
                         "BEGIN SELECT RAISE(ABORT,'fixture'); END")
            conn.commit()
        before = self.path.read_bytes()
        self.assertFalse(self.handoff())
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.disk(), ('uncertain', []))
        self.assertIsNone(self.flow.take_tokens())

    def test_cancel_during_readback_does_not_commit_or_ack(self):
        def readback():
            self.flow.cancel()
            return self.record
        before = self.path.read_bytes()
        self.assertFalse(self.handoff(readback=readback))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.disk(), ('uncertain', []))
        self.assertIsNone(self.flow.take_tokens())

    def test_cancel_after_real_commit_refuses_handoff_without_undo_or_rearm(self):
        parent = self
        class CancelAfterCommit:
            def record_replacement(self, *args, **kwargs):
                ok = parent.fence.record_replacement(*args, **kwargs)
                parent.assertIs(ok, True)
                parent.flow.cancel()
                return ok
        self.assertFalse(self.handoff(fence=CancelAfterCommit()))
        self.assertEqual(self.disk()[0], 'reconciled')
        self.assertEqual(len(self.disk()[1]), 1)
        self.assertIsNone(self.flow.take_tokens())
        self.assertIsNone(self.fence.begin('fixture-new', now=100))
        self.assertIsNone(self.fence.begin('fixture-old', now=100))

    def test_expiry_after_real_commit_refuses_handoff_without_rearm(self):
        parent = self
        class ExpireAfterCommit:
            def record_replacement(self, *args, **kwargs):
                ok = parent.fence.record_replacement(*args, **kwargs)
                parent.assertIs(ok, True)
                parent.clock[0] = 30
                return ok
        self.assertFalse(self.handoff(fence=ExpireAfterCommit()))
        self.assertEqual(self.disk()[0], 'reconciled')
        self.assertEqual(len(self.disk()[1]), 1)
        self.assertIsNone(self.flow.take_tokens())
        self.assertIsNone(self.fence.begin('fixture-old', now=100))
        self.assertIsNone(self.fence.begin('fixture-new', now=100))

    def test_wrong_protected_pair_leaves_uncertainty_and_no_ack(self):
        self.record['pair'] = pair('old')
        before = self.path.read_bytes()
        self.assertFalse(self.handoff())
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNone(self.flow.take_tokens())
        self.assertEqual(self.disk(), ('uncertain', []))

    def test_abrupt_exit_after_commit_before_ack_cold_replay_refused(self):
        code = '''import os, sys
from auth_flow_model import RefreshFlow
from auth_refresh_fence import RefreshFence
from auth_refresh_readback import acknowledge_committed_fixture_readback
from auth_refresh_readback_test import pair
f = RefreshFence(sys.argv[1], 'fixture-slot')
a = sys.argv[2]
flow = RefreshFlow(lambda: 0, pair('old'))
k = flow.start('SYNTHETIC-CLIENT').key
assert flow.receive(k, 200, pair('new'))
class CrashAfterCommit:
    def record_replacement(self, *args, **kwargs):
        assert f.record_replacement(*args, **kwargs) is True
        os._exit(37)
record = dict(slot='fixture-slot', attempt=a, old_revision='fixture-old', revision='fixture-new', expires_at=300, pair=pair('new'))
acknowledge_committed_fixture_readback(flow,k,fence=CrashAfterCommit(),write_ok=True,revision='fixture-new',expires_at=300,old_expires_at=200,now=100,binding={n:record[n] for n in ('slot','attempt','old_revision')},readback=lambda:record)
raise AssertionError('Crash boundary not reached')
'''
        child = subprocess.run([sys.executable, '-B', '-c', code, str(self.path), self.attempt],
                               cwd=Path(__file__).parent, capture_output=True, text=True, timeout=20)
        self.assertEqual(child.returncode, 37, child.stderr)
        self.assertEqual(self.disk()[0], 'reconciled')
        self.assertEqual(len(self.disk()[1]), 1)
        before = self.path.read_bytes()
        self.assertFalse(self.handoff())
        self.assertIsNone(self.flow.take_tokens())
        self.assertEqual(self.path.read_bytes(), before)
        for revision in ('fixture-old', 'fixture-new'):
            self.assertIsNone(self.fence.begin(revision, now=100))


if __name__ == '__main__':
    unittest.main(verbosity=2)
