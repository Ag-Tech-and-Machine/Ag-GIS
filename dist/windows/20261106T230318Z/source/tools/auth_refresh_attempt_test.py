"""Synthetic disk attempt/readback checks; NOT production credential binding."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from auth_refresh_fence import RefreshFence

BASE = Path('C:/Users/Michael/AppData/Local/hermes/cache/scratch')


class AttemptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aggis-attempt-', dir=BASE)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'fence.sqlite3'
        RefreshFence.create(self.path, 'SYNTHETIC-SLOT', revision='fixture-old', expires_at=200)
        self.fence = RefreshFence(self.path, 'SYNTHETIC-SLOT')
        self.attempt = self.fence.begin_bound('fixture-old', expires_at=200, now=100)
        self.assertIsNotNone(self.attempt)

    def test_malformed_identity_or_time_never_calls_readback(self):
        cases = [dict(attempt=None), dict(attempt=''), dict(attempt='A' * 32),
                 dict(revision=None), dict(revision=''), dict(expires_at=True),
                 dict(expires_at=200.0), dict(expires_at=0), dict(expires_at=2**63),
                 dict(now=True), dict(now=100.0), dict(now=0), dict(now=2**63)]
        before = self.path.read_bytes()
        for changed in cases:
            with self.subTest(changed=changed):
                args = dict(attempt=self.attempt, revision='fixture-old', expires_at=200, now=100)
                args.update(changed)
                reads = []
                self.assertIsNone(self.fence.read_attempt(**args, readback=lambda: reads.append(True)))
                self.assertEqual(reads, [], 'Invalid binding must not touch protected storage')
                self.assertEqual(self.path.read_bytes(), before)

    def test_wrong_attempt_slot_metadata_or_expiry_never_reads(self):
        before = self.path.read_bytes()
        cases = [(self.fence, '0' * 32, 'fixture-old', 200, 100),
                 (RefreshFence(self.path, 'OTHER'), self.attempt, 'fixture-old', 200, 100),
                 (self.fence, self.attempt, 'other-revision', 200, 100),
                 (self.fence, self.attempt, 'fixture-old', 201, 100),
                 (self.fence, self.attempt, 'fixture-old', 200, 200)]
        for fence, attempt, revision, expiry, now in cases:
            reads = []
            self.assertIsNone(fence.read_attempt(attempt, revision=revision, expires_at=expiry,
                                                now=now, readback=lambda: reads.append(True)))
            self.assertEqual(reads, [])
            self.assertEqual(self.path.read_bytes(), before)

    def test_unknown_schema_corrupt_missing_and_locked_refuse_without_creation(self):
        before = self.path.read_bytes()
        reads = []
        args = dict(revision='fixture-old', expires_at=200, now=100,
                    readback=lambda: reads.append(True))
        with closing(sqlite3.connect(self.path, timeout=0)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            self.assertIsNone(self.fence.read_attempt(self.attempt, **args))
        self.assertEqual(self.path.read_bytes(), before)
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute('PRAGMA user_version=99')
        unsupported = self.path.read_bytes()
        self.assertIsNone(self.fence.read_attempt(self.attempt, **args))
        self.assertEqual(self.path.read_bytes(), unsupported)
        self.path.write_bytes(b'SYNTHETIC-CORRUPT')
        self.assertIsNone(self.fence.read_attempt(self.attempt, **args))
        self.assertEqual(self.path.read_bytes(), b'SYNTHETIC-CORRUPT')
        self.path.unlink()
        self.assertIsNone(self.fence.read_attempt(self.attempt, **args))
        self.assertFalse(self.path.exists())
        self.assertEqual(reads, [])

    def test_changed_disk_state_or_attempt_refuses(self):
        for column, value in [('state', 'ready'), ('state', 'expired'), ('attempt', '1' * 32),
                              ('expires_at', 'invalid')]:
            with self.subTest(column=column, value=value):
                with closing(sqlite3.connect(self.path)) as conn:
                    conn.execute("UPDATE refresh_fence SET state='uncertain',attempt=?,expires_at=200",
                                 (self.attempt,))
                    conn.execute('UPDATE refresh_fence SET ' + column + '=?', (value,))
                    conn.commit()
                before = self.path.read_bytes()
                reads = []
                self.assertIsNone(self.fence.read_attempt(self.attempt, revision='fixture-old',
                                  expires_at=200, now=100, readback=lambda: reads.append(True)))
                self.assertEqual(reads, [])
                self.assertEqual(self.path.read_bytes(), before)

    def test_writer_lock_held_during_callback_and_released_after_error(self):
        import subprocess
        import sys
        before = self.path.read_bytes()
        code = ("import sqlite3,sys; c=sqlite3.connect(sys.argv[1],timeout=0); "
                "c.execute('BEGIN IMMEDIATE'); print('writer-acquired',flush=True); "
                "c.execute(\"UPDATE refresh_fence SET state='ready'\"); c.commit()")

        def readback():
            child = subprocess.run([sys.executable, '-B', '-c', code, str(self.path)],
                                   capture_output=True, timeout=20)
            self.assertNotEqual(child.returncode, 0)
            self.assertNotIn(b'writer-acquired', child.stdout)
            self.assertIn(b'database is locked', child.stderr)
            raise RuntimeError('SYNTHETIC callback failure')

        with self.assertRaises(RuntimeError):
            self.fence.read_attempt(self.attempt, revision='fixture-old', expires_at=200,
                                    now=100, readback=readback)
        self.assertEqual(self.path.read_bytes(), before)
        with closing(sqlite3.connect(self.path, timeout=0)) as conn:
            conn.execute('BEGIN IMMEDIATE')

    def test_bound_readback_composes_with_model_ack_and_refuses_cross_attempt(self):
        from auth_refresh_readback import acknowledge_fixture_readback
        from auth_refresh_readback_test import ReadbackTests, pair
        for attempt in (self.attempt, '0' * 32):
            flow, key, _ = ReadbackTests().prepare()
            reads = []

            def readback():
                reads.append(True)
                return {'revision': 'fixture-new', 'expires_at': 200, 'pair': pair('new')}

            ack = acknowledge_fixture_readback(flow, key, write_ok=True, revision='fixture-new',
                expires_at=200, readback=lambda: self.fence.read_attempt(
                    attempt, revision='fixture-old', expires_at=200, now=100, readback=readback))
            self.assertIs(ack, attempt == self.attempt)
            self.assertEqual(reads, [True] if ack else [])
            self.assertEqual(flow.take_tokens(), pair('new') if ack else None)

    def test_exact_uncertain_attempt_reads_without_rearm_or_disk_change(self):
        before = self.path.read_bytes()
        reads = []
        record = {'SYNTHETIC': 'replacement'}

        def readback():
            reads.append(True)
            return record

        self.assertTrue(callable(getattr(self.fence, 'read_attempt', None)),
                        'Missing exact-attempt disk readback guard')
        self.assertIs(self.fence.read_attempt(
            self.attempt, revision='fixture-old', expires_at=200, now=100,
            readback=readback), record)
        self.assertEqual(reads, [True])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNone(self.fence.begin_bound('fixture-old', expires_at=200, now=100))


if __name__ == '__main__':
    unittest.main()
