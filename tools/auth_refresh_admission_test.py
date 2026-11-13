"""Synthetic pre-request binding tests; no native storage, network or login."""
from contextlib import closing
from copy import deepcopy
from pathlib import Path
import sqlite3
import tempfile
import unittest

import auth_refresh_readback as gate
from auth_refresh_fence import RefreshFence
from auth_refresh_readback_test import pair

BASE = Path.home() / 'AppData/Local/tool/cache/scratch'


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aggis-pre-request-', dir=BASE)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'fence.sqlite3'
        RefreshFence.create(self.path, 'fixture-slot', revision='fixture-old', expires_at=200)
        self.fence = RefreshFence(self.path, 'fixture-slot')
        self.record = dict(slot='fixture-slot', revision='fixture-old', expires_at=200,
                           attempt='', pair=pair('old'))
        self.now = [100]
        self.writes = []

    def disk(self):
        with closing(sqlite3.connect(self.path)) as conn:
            return conn.execute('SELECT state,attempt,revision,expires_at FROM refresh_fence').fetchone()

    def write(self, record):
        self.assertEqual(self.disk(), ('uncertain', record['attempt'], 'fixture-old', 200))
        with closing(sqlite3.connect(self.path, timeout=0)) as conn:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute('BEGIN IMMEDIATE')
        self.writes.append(deepcopy(record))
        self.record = deepcopy(record)
        return True

    def start(self, readback=None, write=None):
        function = getattr(gate, 'start_bound_fixture_refresh', None)
        self.assertTrue(callable(function), 'Missing pre-request fixture binding gate')
        return function(fence=self.fence, revision='fixture-old', expires_at=200,
                        now=lambda: self.now[0], clock=lambda: 0,
                        client_id='SYNTHETIC-CLIENT', readback=readback or (lambda: self.record),
                        write_bound=write or self.write)

    def test_exact_pair_bound_to_durable_attempt_before_request(self):
        outcome = self.start()
        self.assertIsNotNone(outcome)
        attempt, flow, request = outcome
        self.assertEqual(self.writes, [dict(slot='fixture-slot', revision='fixture-old',
                                          expires_at=200, attempt=attempt, pair=pair('old'))])
        self.assertEqual(self.disk(), ('uncertain', attempt, 'fixture-old', 200))
        self.assertEqual(request.payload['refresh_token'], pair('old')['refresh_token'])
        self.assertIsNone(self.start())
        self.assertEqual(len(self.writes), 1)
        flow.cancel()
        self.assertIsNone(flow.take_tokens())


    def test_changed_original_after_admission_is_not_overwritten(self):
        reads = []
        def read():
            reads.append(True)
            if len(reads) == 2:
                self.record['pair'] = pair('independent-change')
            return self.record
        self.assertIsNone(self.start(readback=read))
        self.assertEqual(self.writes, [])
        self.assertEqual(self.record['pair'], pair('independent-change'))
        self.assertEqual(self.disk()[0], 'uncertain')
        self.assertIsNone(self.fence.begin_bound('fixture-old', expires_at=200, now=100))


    def test_malformed_original_refuses_before_admission_or_write(self):
        before = self.path.read_bytes()
        for field, bad in [('slot', 'other'), ('revision', 'other'), ('expires_at', True),
                           ('attempt', 'a' * 32), ('pair', None)]:
            with self.subTest(field=field):
                original = deepcopy(self.record)
                self.record[field] = bad
                self.assertIsNone(self.start())
                self.record = original
                self.assertEqual(self.path.read_bytes(), before)
        self.record['pair']['extra'] = 'SYNTHETIC-EXTRA'
        self.assertIsNone(self.start())
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.writes, [])

    def test_failed_or_truthy_write_leaves_uncertainty_without_request(self):
        self.assertIsNone(self.start(write=lambda record: 1))
        self.assertEqual(self.disk()[0], 'uncertain')
        self.assertIsNone(self.start())
        self.assertEqual(self.writes, [])

    def test_wrong_pair_in_bound_readback_refuses(self):
        def write(record):
            self.write(record)
            self.record['pair'] = pair('wrong')
            return True
        self.assertIsNone(self.start(write=write))
        self.assertEqual(self.disk()[0], 'uncertain')

    def test_wrong_attempt_in_bound_readback_refuses(self):
        def write(record):
            self.write(record)
            self.record['attempt'] = '0' * 32
            return True
        self.assertIsNone(self.start(write=write))
        self.assertEqual(self.disk()[0], 'uncertain')

    def test_write_cannot_mutate_expected_snapshot(self):
        def write(record):
            record['pair'] = pair('changed-by-writer')
            return self.write(record)
        self.assertIsNone(self.start(write=write))
        self.assertEqual(self.disk()[0], 'uncertain')

    def test_expiry_during_bound_readback_refuses(self):
        reads = []
        def read():
            reads.append(True)
            if len(reads) == 3:
                self.now[0] = 200
            return self.record
        self.assertIsNone(self.start(readback=read))
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(self.disk()[0], 'uncertain')
        self.now[0] = 100
        self.assertIsNone(self.start())

    def test_readback_exception_after_write_refuses_without_replay(self):
        reads = []
        def read():
            reads.append(True)
            if len(reads) == 3:
                raise RuntimeError('SYNTHETIC-CALLBACK-NOT-LOGGED')
            return self.record
        self.assertIsNone(self.start(readback=read))
        self.assertEqual(self.disk()[0], 'uncertain')
        self.assertIsNone(self.start())

    def test_real_writer_lock_refuses_before_native_write(self):
        before = self.path.read_bytes()
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            self.assertIsNone(self.start())
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.writes, [])


if __name__ == '__main__':
    unittest.main()
