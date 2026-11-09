"""Synthetic protected-envelope binding tests, NOT product authentication."""
import unittest

from auth_flow_model import RefreshFlow
import auth_refresh_readback as gate
from auth_refresh_readback_test import pair


class ReceiptTests(unittest.TestCase):
    def prepare(self):
        self.assertTrue(callable(getattr(gate, 'acknowledge_attempt_fixture_readback', None)),
                        'Missing protected-attempt envelope gate')
        clock = [0]
        flow = RefreshFlow(lambda: clock[0], pair('old'))
        request = flow.start('SYNTHETIC-CLIENT')
        assert request is not None
        key = request.key
        self.assertTrue(flow.receive(key, 200, pair('new')))
        binding = {'slot': 'fixture-slot', 'attempt': 'a' * 32, 'old_revision': 'fixture-old'}
        record = dict(binding, revision='fixture-new', expires_at=200, pair=pair('new'))
        return flow, key, clock, binding, record

    def test_exact_envelope_and_wrong_protected_binding(self):
        for field in (None, 'slot', 'attempt', 'old_revision'):
            with self.subTest(field=field):
                flow, key, _, binding, record = self.prepare()
                if field:
                    record[field] = 'b' * 32 if field == 'attempt' else 'other'
                accepted = gate.acknowledge_attempt_fixture_readback(
                    flow, key, write_ok=True, revision='fixture-new', expires_at=200,
                    binding=binding, readback=lambda: record)
                self.assertIs(accepted, field is None)
                self.assertEqual(flow.take_tokens(), None if field else pair('new'))
                self.assertIsNone(flow.take_tokens())
                self.assertEqual(flow.state, 'reauth_required' if field else 'ready')

    def test_invalid_expected_binding_never_reads(self):
        invalid = [None, {}, {'slot': 'fixture-slot'},
                   {'slot': 'fixture-slot', 'attempt': 'A' * 32, 'old_revision': 'fixture-old'},
                   {'slot': '', 'attempt': 'a' * 32, 'old_revision': 'fixture-old'},
                   {'slot': 'fixture-slot', 'attempt': 'a' * 32, 'old_revision': ''},
                   {'slot': 'fixture-slot', 'attempt': 'a' * 32, 'old_revision': 'bad value'},
                   {'slot': 'fixture-slot', 'attempt': True, 'old_revision': 'fixture-old'},
                   {'slot': 'fixture-slot', 'attempt': 'a' * 32, 'old_revision': 'fixture-old', 'extra': 'x'}]
        for index, binding in enumerate(invalid):
            with self.subTest(index=index):
                flow, key, _, _, record = self.prepare()
                reads = []
                def readback():
                    reads.append(True)
                    return record
                self.assertFalse(gate.acknowledge_attempt_fixture_readback(
                    flow, key, write_ok=True, revision='fixture-new', expires_at=200,
                    binding=binding, readback=readback))
                self.assertEqual(reads, [], 'Invalid expected binding must skip protected read')
                self.assertIsNone(flow.take_tokens())
                self.assertEqual(flow.state, 'reauth_required')

    def test_incomplete_or_extra_protected_envelope_refuses(self):
        for field in ('slot', 'attempt', 'old_revision', 'revision', 'expires_at', 'pair', 'extra'):
            flow, key, _, binding, record = self.prepare()
            if field == 'extra':
                record[field] = 'unexpected'
            else:
                del record[field]
            self.assertFalse(gate.acknowledge_attempt_fixture_readback(
                flow, key, write_ok=True, revision='fixture-new', expires_at=200,
                binding=binding, readback=lambda: record))
            self.assertIsNone(flow.take_tokens())
            self.assertEqual(flow.state, 'reauth_required')

    def test_cancel_expiry_exception_and_failed_write_refuse(self):
        for mode in ('cancel', 'expire', 'exception', 'failed-write'):
            flow, key, clock, binding, record = self.prepare()
            reads = []
            def readback():
                reads.append(True)
                if mode == 'cancel':
                    flow.cancel()
                elif mode == 'expire':
                    clock[0] = 30
                elif mode == 'exception':
                    raise RuntimeError('SYNTHETIC-NOT-TO-BE-LOGGED')
                return record
            self.assertFalse(gate.acknowledge_attempt_fixture_readback(
                flow, key, write_ok=mode != 'failed-write', revision='fixture-new', expires_at=200,
                binding=binding, readback=readback))
            self.assertEqual(reads, [] if mode == 'failed-write' else [True])
            self.assertIsNone(flow.take_tokens())
            self.assertEqual(flow.state, 'reauth_required')

    def test_callback_cannot_replace_expected_binding(self):
        flow, key, _, binding, record = self.prepare()
        def readback():
            binding['attempt'] = record['attempt'] = 'b' * 32
            return record
        self.assertFalse(gate.acknowledge_attempt_fixture_readback(
            flow, key, write_ok=True, revision='fixture-new', expires_at=200,
            binding=binding, readback=readback))
        self.assertIsNone(flow.take_tokens())

    def test_wrong_key_and_duplicate_never_read(self):
        flow, key, _, binding, record = self.prepare()
        other, other_key, _, _, _ = self.prepare()
        reads = []
        def readback():
            reads.append(True)
            return record
        kwargs = dict(write_ok=True, revision='fixture-new', expires_at=200,
                      binding=binding, readback=readback)
        self.assertFalse(gate.acknowledge_attempt_fixture_readback(flow, other_key, **kwargs))
        self.assertEqual(reads, [])
        self.assertTrue(gate.acknowledge_attempt_fixture_readback(flow, key, **kwargs))
        self.assertFalse(gate.acknowledge_attempt_fixture_readback(flow, key, **kwargs))
        self.assertEqual(reads, [True])
        self.assertIsNone(other.take_tokens())


if __name__ == '__main__':
    unittest.main()
