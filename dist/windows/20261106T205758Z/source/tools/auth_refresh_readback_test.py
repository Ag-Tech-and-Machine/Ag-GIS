"""Developer-only synthetic readback acknowledgement checks; no real credentials."""
import unittest

from auth_flow_model import RefreshFlow
from auth_refresh_readback import acknowledge_fixture_readback


def pair(suffix):
    return {'access_token': 'SYNTHETIC-access-' + suffix,
            'refresh_token': 'SYNTHETIC-refresh-' + suffix,
            'token_type': 'bearer', 'expires_in': 60, 'refresh_token_expires_in': 100}


class ReadbackTests(unittest.TestCase):
    def prepare(self):
        clock = [0]
        flow = RefreshFlow(lambda: clock[0], pair('old'))
        request = flow.start('SYNTHETIC-CLIENT')
        assert request is not None
        self.assertTrue(flow.receive(request.key, 200, pair('new')))
        return flow, request.key, clock

    def test_exact_readback_before_acknowledgement(self):
        flow, key, _ = self.prepare()
        reads = []

        def readback():
            self.assertIsNone(flow.take_tokens())
            reads.append(True)
            return {'revision': 'fixture-new', 'expires_at': 200, 'pair': pair('new')}

        self.assertTrue(acknowledge_fixture_readback(
            flow, key, write_ok=True, revision='fixture-new', expires_at=200, readback=readback))
        self.assertEqual(reads, [True])
        self.assertEqual(flow.take_tokens(), pair('new'))
        self.assertIsNone(flow.take_tokens())

    def test_stale_mismatched_or_malformed_readback_never_releases_pair(self):
        records = [None, {}, {'revision': 'fixture-old', 'expires_at': 200, 'pair': pair('new')},
                   {'revision': 'fixture-new', 'expires_at': 201, 'pair': pair('new')},
                   {'revision': 'fixture-new', 'expires_at': 200, 'pair': pair('old')},
                   {'revision': 'fixture-new', 'expires_at': 200, 'pair': dict(pair('new'), expires_in=True)},
                   {'revision': 'fixture-new', 'expires_at': 200, 'pair': dict(pair('new'), extra='unknown')},
                   {'revision': 'fixture-new', 'expires_at': '200', 'pair': pair('new')}]
        for record in records:
            with self.subTest(record=records.index(record)):
                flow, key, _ = self.prepare()
                self.assertFalse(acknowledge_fixture_readback(
                    flow, key, write_ok=True, revision='fixture-new', expires_at=200,
                    readback=lambda: record))
                self.assertIsNone(flow.take_tokens())
                self.assertEqual(flow.state, 'reauth_required')

    def test_failed_write_and_readback_exception_fail_closed(self):
        for write_ok in (False, 1, 'true', None, True):
            flow, key, _ = self.prepare()
            reads = []

            def readback():
                reads.append(True)
                raise RuntimeError('SYNTHETIC-DO-NOT-LOG')

            self.assertFalse(acknowledge_fixture_readback(
                flow, key, write_ok=write_ok, revision='fixture-new', expires_at=200,
                readback=readback))
            self.assertEqual(reads, [True] if write_ok is True else [])
            self.assertIsNone(flow.take_tokens())
            self.assertEqual(flow.state, 'reauth_required')

    def test_cancel_or_expire_during_exact_readback_refuses_late_ack(self):
        for stop in ('cancel', 'expire'):
            flow, key, clock = self.prepare()

            def readback():
                if stop == 'cancel':
                    flow.cancel()
                else:
                    clock[0] = 30
                return {'revision': 'fixture-new', 'expires_at': 200, 'pair': pair('new')}

            self.assertFalse(acknowledge_fixture_readback(
                flow, key, write_ok=True, revision='fixture-new', expires_at=200,
                readback=readback))
            self.assertIsNone(flow.take_tokens())
            self.assertEqual(flow.state, 'reauth_required')

    def test_wrong_flow_key_or_duplicate_never_reads_storage(self):
        flow, key, _ = self.prepare()
        other, other_key, _ = self.prepare()
        reads = []

        def readback():
            reads.append(True)
            return {'revision': 'fixture-new', 'expires_at': 200, 'pair': pair('new')}

        self.assertFalse(acknowledge_fixture_readback(
            flow, other_key, write_ok=True, revision='fixture-new', expires_at=200,
            readback=readback))
        self.assertEqual(reads, [])
        self.assertTrue(acknowledge_fixture_readback(
            flow, key, write_ok=True, revision='fixture-new', expires_at=200, readback=readback))
        self.assertFalse(acknowledge_fixture_readback(
            flow, key, write_ok=True, revision='fixture-new', expires_at=200, readback=readback))
        self.assertEqual(reads, [True])
        self.assertIsNone(other.take_tokens())

    def test_invalid_expected_metadata_is_not_an_acknowledgement(self):
        for revision, expiry in (('', 200), (None, 200), ('fixture-new', True),
                                 ('fixture-new', 0), ('fixture-new', 2**63)):
            flow, key, _ = self.prepare()
            self.assertFalse(acknowledge_fixture_readback(
                flow, key, write_ok=True, revision=revision, expires_at=expiry,
                readback=lambda: {'revision': revision, 'expires_at': expiry, 'pair': pair('new')}))
            self.assertIsNone(flow.take_tokens())
            self.assertEqual(flow.state, 'reauth_required')


if __name__ == '__main__':
    unittest.main()
