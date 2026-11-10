"""Developer-only synthetic disk fence; no native auth, tokens or network."""
from contextlib import closing
import importlib
import importlib.util
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class FenceTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('auth_refresh_fence'),
                             'Durable pre-request fence is not implemented')
        self.Fence = importlib.import_module('auth_refresh_fence').RefreshFence
        # The scheduler can supply system TEMP despite the advertised scratch root.
        scratch = Path.home() / 'AppData/Local/tool/cache/scratch'
        self.assertTrue(scratch.is_dir())
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-refresh-fence-', dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'fence.sqlite3'

    def child(self, code, *args):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([sys.executable, '-B', '-c', code, str(self.path), *args],
                                cwd=Path(__file__).parent, env=env, capture_output=True,
                                text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_committed_admission_survives_abrupt_exit_and_refuses_cold_retry(self):
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        self.child('from auth_refresh_fence import RefreshFence; import os,sys; '
                   'assert RefreshFence(sys.argv[1], "fixture-slot").begin("fixture-revision", now=100); os._exit(0)')
        self.assertEqual(self.child('from auth_refresh_fence import RefreshFence; import sys; '
                                   'print(RefreshFence(sys.argv[1], "fixture-slot").begin("fixture-revision", now=100) is None)'),
                         'True')
        with closing(sqlite3.connect(self.path)) as conn:
            row = conn.execute('SELECT slot,state,attempt FROM refresh_fence').fetchone()
        self.assertEqual(row[:2], ('fixture-slot', 'uncertain'))
        self.assertEqual(len(row[2]), 32)
        self.assertEqual(set(p.name for p in self.path.parent.iterdir()), {'fence.sqlite3'})


    def test_bound_admission_requires_exact_readback_expiry(self):
        self.assertTrue(callable(getattr(self.Fence, 'begin_bound', None)),
                        'Readback expiry admission guard is not implemented')
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        fence = self.Fence(self.path, 'fixture-slot')
        before = self.path.read_bytes()
        for revision, expiry in (('fixture-revision', 201), ('fixture-revision', 199),
                                 ('WRONG-REVISION', 200)):
            self.assertIsNone(fence.begin_bound(revision, expires_at=expiry, now=100))
            self.assertEqual(self.path.read_bytes(), before)
        attempt = fence.begin_bound('fixture-revision', expires_at=200, now=100)
        self.assertIsNotNone(attempt)
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT state,attempt,revision,expires_at '
                                          'FROM refresh_fence').fetchone(),
                             ('uncertain', attempt, 'fixture-revision', 200))
        self.assertIsNone(fence.begin_bound('fixture-revision', expires_at=200, now=100))

    def test_bound_invalid_expiry_never_uses_unbound_fallback(self):
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        before = self.path.read_bytes()
        for expiry in (None, True, 200.0, '200', 0, -1, 2**63):
            self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin_bound(
                'fixture-revision', expires_at=expiry, now=100))
            self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNotNone(self.Fence(self.path, 'fixture-slot').begin_bound(
            'fixture-revision', expires_at=200, now=100))

    def test_bound_mismatch_cannot_latch_expiry_but_exact_cold_observation_does(self):
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        before = self.path.read_bytes()
        fence = self.Fence(self.path, 'fixture-slot')
        self.assertIsNone(fence.begin_bound('fixture-revision', expires_at=201, now=200))
        self.assertEqual(self.path.read_bytes(), before)
        self.child('from auth_refresh_fence import RefreshFence; import os,sys; '
                   'assert RefreshFence(sys.argv[1], "fixture-slot").begin_bound('
                   '"fixture-revision", expires_at=200, now=200) is None; os._exit(0)')
        self.assertEqual(self.child('from auth_refresh_fence import RefreshFence; import sys; '
                         'print(RefreshFence(sys.argv[1], "fixture-slot").begin_bound('
                         '"fixture-revision", expires_at=200, now=100) is None)'), 'True')
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT state,attempt FROM refresh_fence').fetchone(),
                             ('expired', ''))

    def test_bound_lock_wrong_slot_and_schema_refuse_without_write(self):
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        before = self.path.read_bytes()
        self.assertIsNone(self.Fence(self.path, 'wrong-slot').begin_bound(
            'fixture-revision', expires_at=200, now=100))
        self.assertEqual(self.path.read_bytes(), before)
        with closing(sqlite3.connect(self.path)) as writer:
            writer.execute('BEGIN IMMEDIATE')
            self.assertEqual(self.child('from auth_refresh_fence import RefreshFence; import sys; '
                             'print(RefreshFence(sys.argv[1], "fixture-slot").begin_bound('
                             '"fixture-revision", expires_at=200, now=100) is None)'), 'True')
            self.assertEqual(self.path.read_bytes(), before)
            writer.rollback()
            writer.execute('PRAGMA user_version=999')
        before = self.path.read_bytes()
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin_bound(
            'fixture-revision', expires_at=200, now=100))
        self.assertEqual(self.path.read_bytes(), before)

    def test_locked_writer_refuses_admission_without_changing_disk(self):
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        before = self.path.read_bytes()
        with closing(sqlite3.connect(self.path)) as writer:
            writer.execute('BEGIN IMMEDIATE')
            self.assertEqual(self.child('from auth_refresh_fence import RefreshFence; import sys; '
                                       'print(RefreshFence(sys.argv[1], "fixture-slot").begin("fixture-revision", now=100) is None)'),
                             'True')
            self.assertEqual(self.path.read_bytes(), before)
            writer.rollback()
        self.assertIsNotNone(self.Fence(self.path, 'fixture-slot').begin("fixture-revision", now=100))
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin("fixture-revision", now=100))

    def test_two_process_contenders_never_double_admit_and_cold_state_matches(self):
        code = ('from auth_refresh_fence import RefreshFence; import sys,os,json; '
                'sys.stdin.readline(); '
                'attempt=RefreshFence(sys.argv[1], "fixture-slot").begin("fixture-revision", now=100); '
                'print(json.dumps({"pid":os.getpid(), "attempt":attempt, "admitted":attempt is not None}))')
        import json
        for round_number in range(5):
            path = self.path.with_name(f'race-{round_number}.sqlite3')
            self.Fence.create(path, 'fixture-slot', revision='fixture-revision', expires_at=200)
            children = [subprocess.Popen([sys.executable, '-B', '-c', code, str(path)],
                        cwd=Path(__file__).parent, stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        for _ in range(2)]
            try:
                for child in children:
                    assert child.stdin is not None
                    child.stdin.write('go\n')
                    child.stdin.flush()
                rows = []
                for child in children:
                    stdout, stderr = child.communicate(timeout=20)
                    self.assertEqual(child.returncode, 0, stderr)
                    rows.append(json.loads(stdout))
                self.assertEqual(len({row['pid'] for row in rows}), 2)
                with closing(sqlite3.connect(path)) as observer:
                    disk = observer.execute('SELECT state,attempt,revision,expires_at FROM refresh_fence').fetchone()
                admitted = [row for row in rows if row['admitted']]
                self.assertLessEqual(len(admitted), 1, (rows, disk))
                if admitted:
                    self.assertEqual(disk, ('uncertain', admitted[0]['attempt'], 'fixture-revision', 200))
                else:
                    # timeout=0 is fail-closed, not an exactly-one liveness promise.
                    # Both may refuse; only a byte-valid ready row permits a serial admission.
                    self.assertEqual(disk, ('ready', '', 'fixture-revision', 200))
                    attempt = self.Fence(path, 'fixture-slot').begin('fixture-revision', now=100)
                    self.assertIsNotNone(attempt)
                    with closing(sqlite3.connect(path)) as observer:
                        self.assertEqual(observer.execute('SELECT state,attempt FROM refresh_fence').fetchone(),
                                         ('uncertain', attempt))
                self.assertIsNone(self.Fence(path, 'fixture-slot').begin("fixture-revision", now=100))
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()  # test-owned synthetic helper only
                    child.communicate(timeout=20)

    def test_missing_corrupt_unknown_schema_and_wrong_slot_fail_closed(self):
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin("fixture-revision", now=100))
        self.assertFalse(self.path.exists(), 'Missing fence must never be auto-created')
        self.path.write_bytes(b'synthetic non-sqlite fixture')
        before = self.path.read_bytes()
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin("fixture-revision", now=100))
        self.assertEqual(self.path.read_bytes(), before)
        self.path.unlink()
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        before = self.path.read_bytes()
        self.assertIsNone(self.Fence(self.path, 'other-fixture-slot').begin("fixture-revision", now=100))
        self.assertEqual(self.path.read_bytes(), before)
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute('PRAGMA user_version=999')
        before = self.path.read_bytes()
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin("fixture-revision", now=100))
        self.assertEqual(self.path.read_bytes(), before)

    def test_exact_revision_refuses_stale_caller_without_consuming_admission(self):
        import inspect
        self.assertIn('revision', inspect.signature(self.Fence.create).parameters,
                      'Exact revision binding is not implemented')
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        before = self.path.read_bytes()
        for stale in ('other-revision', 'FIXTURE-REVISION', '', None, True):
            self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin(stale, now=100))
            self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNotNone(self.Fence(self.path, 'fixture-slot').begin('fixture-revision', now=100))
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin('fixture-revision', now=100))
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT revision FROM refresh_fence').fetchone(),
                             ('fixture-revision',))

    def test_absolute_expiry_is_read_from_disk_at_cold_admission(self):
        import inspect
        self.assertIn('expires_at', inspect.signature(self.Fence.create).parameters,
                      'Persisted absolute expiry is not implemented')
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        before = self.path.read_bytes()
        # Malformed clock observations must not consume a ready fixture. A valid
        # expiry observation now intentionally latches; see the cold-restart test.
        for now in (True, -1, 0, 199.0, '199', None, float('inf'), 2**63):
            code = ('from auth_refresh_fence import RefreshFence; import sys; '
                    'print(RefreshFence(sys.argv[1], "fixture-slot").begin('
                    f'"fixture-revision", now={repr(now) if now != float("inf") else "float(\'inf\')"}) is None)')
            self.assertEqual(self.child(code), 'True')
            self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.child('from auth_refresh_fence import RefreshFence; import sys; '
                         'print(RefreshFence(sys.argv[1], "fixture-slot").begin('
                         '"fixture-revision", now=199) is not None)'), 'True')
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin('fixture-revision', now=1))
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT expires_at,state FROM refresh_fence').fetchone(),
                             (200, 'uncertain'))

    def test_observed_expiry_survives_abrupt_exit_and_backward_clock(self):
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        self.child('from auth_refresh_fence import RefreshFence; import os,sys; '
                   'assert RefreshFence(sys.argv[1], "fixture-slot").begin('
                   '"fixture-revision", now=200) is None; os._exit(0)')
        after = self.path.read_bytes()
        self.assertEqual(self.child('from auth_refresh_fence import RefreshFence; import sys; '
                         'print(RefreshFence(sys.argv[1], "fixture-slot").begin('
                         '"fixture-revision", now=100) is None)'), 'True',
                         'Observed expiry must not resurrect after backward clock/cold restart')
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT state,attempt,revision,expires_at '
                                          'FROM refresh_fence').fetchone(),
                             ('expired', '', 'fixture-revision', 200))
        self.assertEqual(self.path.read_bytes(), after)
        with self.assertRaises(FileExistsError):
            self.Fence.create(self.path, 'fixture-slot', revision='replacement', expires_at=300)
        self.assertEqual(self.path.read_bytes(), after)

    def test_unrelated_or_locked_expiry_observation_does_not_latch(self):
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        before = self.path.read_bytes()
        for slot, revision in (('wrong-slot', 'fixture-revision'),
                               ('fixture-slot', 'WRONG-REVISION')):
            self.assertIsNone(self.Fence(self.path, slot).begin(revision, now=201))
            self.assertEqual(self.path.read_bytes(), before)
        with closing(sqlite3.connect(self.path)) as writer:
            writer.execute('BEGIN IMMEDIATE')
            self.assertEqual(self.child('from auth_refresh_fence import RefreshFence; import sys; '
                             'print(RefreshFence(sys.argv[1], "fixture-slot").begin('
                             '"fixture-revision", now=201) is None)'), 'True')
            self.assertEqual(self.path.read_bytes(), before)
            writer.rollback()
        # A failed disk write is NOT a durable observation; a trustworthy-clock
        # production adapter must refuse dispatch independently of this fixture.
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin('fixture-revision', now=201))
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin('fixture-revision', now=199))
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT state,attempt FROM refresh_fence').fetchone(),
                             ('expired', ''))

    def test_invalid_binding_or_expiry_never_creates_or_consumes_a_fence(self):
        invalid_revisions = ('', ' ', '\x00', 'x' * 129, True, 1, None, b'fixture')
        for revision in invalid_revisions:
            with self.assertRaises(ValueError):
                self.Fence.create(self.path, 'fixture-slot', revision=revision, expires_at=200)
            self.assertFalse(self.path.exists())
        for expiry in (True, 0, -1, 200.0, '200', None, 2**63):
            with self.assertRaises(ValueError):
                self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision',
                                  expires_at=expiry)
            self.assertFalse(self.path.exists())
        self.Fence.create(self.path, 'fixture-slot', revision='1', expires_at=200)
        before = self.path.read_bytes()
        for revision in invalid_revisions:
            self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin(revision, now=100))
            self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNotNone(self.Fence(self.path, 'fixture-slot').begin('1', now=100))

    def test_legacy_schema_and_malformed_disk_expiry_refuse_without_migration(self):
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        for version in (1, 2, 999):
            with closing(sqlite3.connect(self.path)) as conn:
                conn.execute(f'PRAGMA user_version={version}')
            before = self.path.read_bytes()
            self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin('fixture-revision', now=100))
            self.assertEqual(self.path.read_bytes(), before)
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute('PRAGMA user_version=3')
        for expiry in ('unknown', b'200', 200.5, -1):
            with closing(sqlite3.connect(self.path)) as conn:
                conn.execute('UPDATE refresh_fence SET expires_at=?', (expiry,))
                conn.commit()
            before = self.path.read_bytes()
            self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin('fixture-revision', now=100))
            self.assertEqual(self.path.read_bytes(), before)

    def test_explicit_enrollment_cannot_overwrite_or_rearm_uncertain_slot(self):
        self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        self.assertIsNotNone(self.Fence(self.path, 'fixture-slot').begin("fixture-revision", now=100))
        before = self.path.read_bytes()
        with self.assertRaises(FileExistsError):
            self.Fence.create(self.path, 'fixture-slot', revision='fixture-revision', expires_at=200)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNone(self.Fence(self.path, 'fixture-slot').begin("fixture-revision", now=100))


if __name__ == '__main__':
    unittest.main(verbosity=2)
