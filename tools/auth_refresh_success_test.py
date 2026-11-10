"""Synthetic terminal replacement receipts; NOT native storage or usable login."""
from contextlib import closing
from pathlib import Path
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from auth_refresh_fence import RefreshFence

BASE = Path.home() / 'AppData/Local/tool/cache/scratch'


class SuccessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aggis-success-', dir=BASE)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'fence.sqlite3'
        RefreshFence.create(self.path, 'fixture-slot', revision='fixture-old', expires_at=200)
        self.fence = RefreshFence(self.path, 'fixture-slot')
        self.attempt = self.fence.begin_bound('fixture-old', expires_at=200, now=100)
        self.assertIsNotNone(self.attempt)

    def receipt(self):
        return dict(slot='fixture-slot', attempt=self.attempt, old_revision='fixture-old',
                    revision='fixture-new', expires_at=300)

    def reconcile(self, readback=None, **changed):
        self.assertTrue(callable(getattr(self.fence, 'record_replacement', None)),
                        'Missing durable terminal replacement receipt')
        args = dict(revision='fixture-old', expires_at=200, now=100,
                    replacement_revision='fixture-new', replacement_expires_at=300,
                    readback=readback or self.receipt)
        args.update(changed)
        return self.fence.record_replacement(self.attempt, **args)

    def test_committed_terminal_receipt_survives_cold_process_and_never_rearms(self):
        self.assertIs(self.reconcile(), True)
        expected = ('fixture-slot', self.attempt, 'fixture-old', 200, 'fixture-new', 300)
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT * FROM refresh_replacement').fetchone(), expected)
            self.assertEqual(conn.execute('SELECT state,attempt,revision,expires_at FROM refresh_fence').fetchone(),
                             ('reconciled', self.attempt, 'fixture-old', 200))
        before = self.path.read_bytes()
        child_code = ('import sys,sqlite3,json; from auth_refresh_fence import RefreshFence; '
                      'f=RefreshFence(sys.argv[1],"fixture-slot"); '
                      'assert f.begin("fixture-old",now=100) is None; '
                      'assert f.begin("fixture-new",now=100) is None; '
                      'c=sqlite3.connect(sys.argv[1]); '
                      'print(json.dumps(c.execute("SELECT * FROM refresh_replacement").fetchone())); c.close()')
        child = subprocess.run([sys.executable, '-B', '-c', child_code, str(self.path)],
                               cwd=Path(__file__).parent, capture_output=True, text=True, timeout=20)
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertEqual(tuple(json.loads(child.stdout)), expected)
        self.assertEqual(self.path.read_bytes(), before)
        reads = []
        self.assertFalse(self.reconcile(readback=lambda: reads.append(True)))
        self.assertEqual(reads, [], 'Terminal receipt must not allow replay or another protected read')
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual({p.name for p in self.path.parent.iterdir()}, {'fence.sqlite3'})


    def test_wrong_or_secret_bearing_metadata_refuses_without_disk_write(self):
        before = self.path.read_bytes()
        for field in ('slot', 'attempt', 'old_revision', 'revision', 'expires_at', 'missing', 'pair'):
            with self.subTest(field=field):
                record = self.receipt()
                if field == 'missing':
                    del record['attempt']
                elif field == 'pair':
                    record['pair'] = {'access_token': 'SYNTHETIC-NOT-TO-BE-PERSISTED'}
                else:
                    record[field] = 301 if field == 'expires_at' else 'wrong'
                self.assertFalse(self.reconcile(readback=lambda: record))
                self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(self.reconcile(readback=lambda: True))
        def failed_read():
            raise RuntimeError('SYNTHETIC-NOT-TO-BE-LOGGED')
        self.assertFalse(self.reconcile(readback=failed_read))
        self.assertEqual(self.path.read_bytes(), before)

    def test_malformed_or_stale_expectations_skip_readback(self):
        cases = [dict(revision='wrong'), dict(expires_at=201), dict(now=200),
                 dict(now=True), dict(now=0), dict(now=2**63), dict(expires_at=None),
                 dict(replacement_revision='fixture-old'), dict(replacement_revision='bad value'),
                 dict(replacement_expires_at=100), dict(replacement_expires_at=True),
                 dict(replacement_expires_at=300.0), dict(replacement_expires_at=2**63)]
        before = self.path.read_bytes()
        for changed in cases:
            reads = []
            self.assertFalse(self.reconcile(readback=lambda: reads.append(True), **changed))
            self.assertEqual(reads, [])
            self.assertEqual(self.path.read_bytes(), before)
        original = self.attempt
        reads = []
        self.attempt = '0' * 32
        self.assertFalse(self.reconcile(readback=lambda: reads.append(True)))
        self.attempt = original
        self.fence = RefreshFence(self.path, 'other-slot')
        self.assertFalse(self.reconcile(readback=lambda: reads.append(True)))
        self.assertEqual(reads, [], 'Wrong attempt/slot must not read protected storage')
        self.assertEqual(self.path.read_bytes(), before)

    def test_unknown_schema_missing_corrupt_and_writer_locked_skip_read(self):
        reads = []
        readback = lambda: reads.append(True)
        before = self.path.read_bytes()
        with closing(sqlite3.connect(self.path, timeout=0)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            self.assertFalse(self.reconcile(readback=readback))
        self.assertEqual(self.path.read_bytes(), before)
        for version in (1, 2, 99):
            with closing(sqlite3.connect(self.path)) as conn:
                conn.execute(f'PRAGMA user_version={version}')
            before = self.path.read_bytes()
            self.assertFalse(self.reconcile(readback=readback))
            self.assertEqual(self.path.read_bytes(), before)
        self.path.write_bytes(b'SYNTHETIC-CORRUPT')
        self.assertFalse(self.reconcile(readback=readback))
        self.assertEqual(self.path.read_bytes(), b'SYNTHETIC-CORRUPT')
        self.path.unlink()
        self.assertFalse(self.reconcile(readback=readback))
        self.assertFalse(self.path.exists())
        self.assertEqual(reads, [])

    def test_actual_update_failure_rolls_back_insert_and_keeps_uncertainty(self):
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute("CREATE TRIGGER refuse_terminal BEFORE UPDATE ON refresh_fence "
                         "WHEN NEW.state='reconciled' BEGIN SELECT RAISE(ABORT,'fixture-refusal'); END")
            conn.commit()
        before = self.path.read_bytes()
        self.assertFalse(self.reconcile())
        self.assertEqual(self.path.read_bytes(), before)
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM refresh_replacement').fetchone(), (0,))
            self.assertEqual(conn.execute('SELECT state FROM refresh_fence').fetchone(), ('uncertain',))

    def test_commit_busy_rolls_back_without_success(self):
        # Real SHARED reader allows BEGIN IMMEDIATE and writes but blocks commit.
        with closing(sqlite3.connect(self.path, timeout=0)) as reader:
            reader.execute('BEGIN')
            reader.execute('SELECT * FROM refresh_fence').fetchall()
            before = self.path.read_bytes()
            self.assertFalse(self.reconcile())
            self.assertEqual(self.path.read_bytes(), before)
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM refresh_replacement').fetchone(), (0,))
            self.assertEqual(conn.execute('SELECT state FROM refresh_fence').fetchone(), ('uncertain',))
        self.assertTrue(self.reconcile())

    def test_writer_reservation_held_through_callback(self):
        code = ('import sqlite3,sys; c=sqlite3.connect(sys.argv[1],timeout=0); '
                'c.execute("BEGIN IMMEDIATE"); print("writer-acquired",flush=True)')
        def readback():
            child = subprocess.run([sys.executable, '-B', '-c', code, str(self.path)],
                                   capture_output=True, text=True, timeout=20)
            self.assertNotEqual(child.returncode, 0)
            self.assertNotIn('writer-acquired', child.stdout)
            self.assertIn('database is locked', child.stderr)
            return self.receipt()
        self.assertTrue(self.reconcile(readback=readback))

    def test_abrupt_exit_before_and_after_commit_keeps_coherent_state(self):
        code = ('import os,sys; from auth_refresh_fence import RefreshFence; '
                'f=RefreshFence(sys.argv[1],"fixture-slot"); '
                'a=sys.argv[2]; mode=sys.argv[3]; '
                'r=dict(slot="fixture-slot",attempt=a,old_revision="fixture-old",revision="fixture-new",expires_at=300); '
                'assert f.record_replacement(a,revision="fixture-old",expires_at=200,now=100,'
                'replacement_revision="fixture-new",replacement_expires_at=300,'
                'readback=(lambda: os._exit(0)) if mode=="before" else (lambda:r)); os._exit(0)')
        for mode in ('before', 'after'):
            child = subprocess.run([sys.executable, '-B', '-c', code, str(self.path), self.attempt, mode],
                                   cwd=Path(__file__).parent, capture_output=True, text=True, timeout=20)
            self.assertEqual(child.returncode, 0, child.stderr)
            with closing(sqlite3.connect(self.path)) as conn:
                self.assertEqual(conn.execute('SELECT state FROM refresh_fence').fetchone(),
                                 ('uncertain' if mode == 'before' else 'reconciled',))
                self.assertEqual(conn.execute('SELECT count(*) FROM refresh_replacement').fetchone(),
                                 (0 if mode == 'before' else 1,))
            self.assertIsNone(self.fence.begin('fixture-old', now=100))
            self.assertIsNone(self.fence.begin('fixture-new', now=100))


if __name__ == '__main__':
    unittest.main(verbosity=2)
