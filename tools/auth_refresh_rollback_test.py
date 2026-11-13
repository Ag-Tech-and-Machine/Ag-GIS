"""Characterize UNFIXED clock/snapshot limits, not production rollback protection.

Only nonsecret SQLite fixtures in your agent scratch. No native credential store,
OS clock change, network, model token, real profile or product action is used.
Expected admissions AFTER deliberate snapshot rollback document unsafe boundaries;
a passing suite must never be described as a rollback defense.
"""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from auth_refresh_fence import RefreshFence

BASE = Path.home() / 'AppData/Local/tool/cache/scratch'
TOOLS = Path(__file__).resolve().parent

# Each call starts a fresh interpreter and independently opens the fixture on disk.
CHILD = '''
from contextlib import closing
import json, os, sqlite3, sys
from auth_refresh_fence import RefreshFence
path, action, now, attempt = sys.argv[1:]
f = RefreshFence(path, 'fixture-slot')
reads = []
if action == 'begin':
    result = f.begin_bound('fixture-old', expires_at=200, now=int(now))
elif action == 'read':
    def readback():
        reads.append(True)
        return 'nonsecret-read-marker'
    result = f.read_attempt(attempt, revision='fixture-old', expires_at=200,
                            now=int(now), readback=readback)
else:
    raise AssertionError('Unknown fixture action')
with closing(sqlite3.connect(path)) as c:
    assert c.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    row = c.execute('SELECT * FROM refresh_fence').fetchone()
    receipts = c.execute('SELECT * FROM refresh_replacement').fetchall()
print(json.dumps(dict(pid=os.getpid(), result=result, reads=len(reads),
                     row=row, receipts=receipts)))
'''


class RollbackBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(BASE.is_dir())
        self.temp = tempfile.TemporaryDirectory(prefix='aggis-rollback-boundary-', dir=BASE)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'fixture.sqlite3'
        RefreshFence.create(self.path, 'fixture-slot', revision='fixture-old', expires_at=200)
        self.ready_snapshot = self.path.read_bytes()
        self.assert_disk('ready', '')
        self.pids = set()

    def assert_disk(self, state, attempt, receipts=()):
        with closing(sqlite3.connect(self.path)) as c:
            self.assertEqual(c.execute('PRAGMA integrity_check').fetchone(), ('ok',))
            self.assertEqual(c.execute('SELECT * FROM refresh_fence').fetchone(),
                             ('fixture-slot', state, attempt, 'fixture-old', 200))
            self.assertEqual(c.execute('SELECT * FROM refresh_replacement').fetchall(), list(receipts))
        self.assertEqual({p.name for p in self.path.parent.iterdir()}, {'fixture.sqlite3'})

    def child(self, *, now=100, action='begin', attempt=''):
        result = subprocess.run([sys.executable, '-B', '-c', CHILD, str(self.path),
                                 action, str(now), attempt], cwd=TOOLS,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads(result.stdout)
        self.assertNotEqual(row['pid'], os.getpid())
        self.assertNotIn(row['pid'], self.pids)
        self.pids.add(row['pid'])
        return row

    def assert_admitted(self, row):
        attempt = row['result']
        self.assertIs(type(attempt), str)
        self.assertEqual(len(attempt), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in attempt))
        self.assertEqual(row['row'], ['fixture-slot', 'uncertain', attempt, 'fixture-old', 200])
        self.assertEqual(row['receipts'], [])
        self.assert_disk('uncertain', attempt)
        return attempt

    def restore_fixture(self, snapshot):
        # All database connections/children are closed. Deliberate fixture-only
        # replacement represents an external restore, NOT supported fence rearm.
        self.assertNotEqual(self.path.read_bytes(), snapshot)
        self.path.write_bytes(snapshot)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).digest(),
                         hashlib.sha256(snapshot).digest())

    def reconcile_fixture(self, attempt):
        self.assertIs(RefreshFence(self.path, 'fixture-slot').record_replacement(
            attempt, revision='fixture-old', expires_at=200, now=100,
            replacement_revision='fixture-new', replacement_expires_at=300,
            readback=lambda: dict(slot='fixture-slot', attempt=attempt,
                                 old_revision='fixture-old', revision='fixture-new', expires_at=300)), True)
        receipts = [('fixture-slot', attempt, 'fixture-old', 200, 'fixture-new', 300)]
        self.assert_disk('reconciled', attempt, receipts)
        return receipts

    def test_unobserved_expiry_with_stale_injected_time_still_admits_known_gap(self):
        reference_now = 201  # Independent test expectation; never changes OS time.
        stale_now = 100
        self.assertGreaterEqual(reference_now, 200)
        self.assertLess(stale_now, 200)
        self.assert_admitted(self.child(now=stale_now))
        # The guard never receives reference_now: no trusted-time claim is possible.
        self.assertIsNone(self.child(now=reference_now)['result'])

    def test_forward_clock_latch_is_not_undone_by_corrected_time(self):
        corrected_now = 100
        self.assertIsNone(self.child(now=201)['result'])
        self.assert_disk('expired', '')
        after = self.path.read_bytes()
        self.assertIsNone(self.child(now=corrected_now)['result'])
        self.assert_disk('expired', '')
        self.assertEqual(self.path.read_bytes(), after)

    def test_restored_ready_snapshot_erases_observed_expiry_known_gap(self):
        self.assertIsNone(self.child(now=200)['result'])
        self.assert_disk('expired', '')
        self.assertIsNone(self.child(now=100)['result'])
        self.restore_fixture(self.ready_snapshot)
        self.assert_disk('ready', '')
        self.assert_admitted(self.child(now=100))

    def test_restored_ready_snapshot_permits_second_attempt_known_gap(self):
        first = self.assert_admitted(self.child())
        before = self.path.read_bytes()
        self.assertIsNone(self.child()['result'])
        self.assertEqual(self.path.read_bytes(), before)
        self.restore_fixture(self.ready_snapshot)
        second = self.assert_admitted(self.child())
        self.assertNotEqual(first, second)
        self.assertIsNone(self.child()['result'])

    def test_restored_ready_snapshot_loses_terminal_receipt_known_gap(self):
        first = self.assert_admitted(self.child())
        receipts = self.reconcile_fixture(first)
        before = self.path.read_bytes()
        self.assertIsNone(self.child()['result'])
        self.assert_disk('reconciled', first, receipts)
        self.assertEqual(self.path.read_bytes(), before)
        self.restore_fixture(self.ready_snapshot)
        second = self.assert_admitted(self.child())
        self.assertNotEqual(first, second)

    def test_restored_uncertain_snapshot_replays_readback_callback_known_gap(self):
        attempt = self.assert_admitted(self.child())
        uncertain_snapshot = self.path.read_bytes()
        receipts = self.reconcile_fixture(attempt)
        before = self.path.read_bytes()
        refused = self.child(action='read', attempt=attempt)
        self.assertIsNone(refused['result'])
        self.assertEqual(refused['reads'], 0)
        self.assert_disk('reconciled', attempt, receipts)
        self.assertEqual(self.path.read_bytes(), before)
        self.restore_fixture(uncertain_snapshot)
        self.assert_disk('uncertain', attempt)
        replayed = self.child(action='read', attempt=attempt)
        self.assertEqual(replayed['result'], 'nonsecret-read-marker')
        self.assertEqual(replayed['reads'], 1)
        self.assert_disk('uncertain', attempt)
        self.assertEqual(self.path.read_bytes(), uncertain_snapshot)
        self.assertIsNone(self.child()['result'])
        # Callback replay is NOT a model handoff, a native read or a second begin.


if __name__ == '__main__':
    unittest.main(verbosity=2)
