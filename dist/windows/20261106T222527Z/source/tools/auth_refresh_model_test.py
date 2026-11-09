"""Synthetic refresh reconciliation only; no native store, network or product UI."""
import unittest
from auth_flow_model import RefreshFlow
from auth_flow_model_test import Clock, token


class RefreshTest(unittest.TestCase):
    def test_rotated_pair_not_available_until_exact_save_acknowledgement(self):
        clock = Clock()
        flow = RefreshFlow(clock, token())
        request = flow.start('SYNTHETIC-CLIENT')
        self.assertEqual(request.payload, {'client_id': 'SYNTHETIC-CLIENT',
                         'grant_type': 'refresh_token', 'refresh_token': token()['refresh_token']})
        self.assertIsNone(flow.start('SYNTHETIC-CLIENT'))
        self.assertIsNone(flow.take_tokens())
        rotated = dict(token(), access_token='SYNTHETIC-NEW-ACCESS', refresh_token='SYNTHETIC-NEW-REFRESH')
        self.assertTrue(flow.receive(request.key, 200, rotated))
        self.assertEqual(flow.state, 'awaiting_save')
        self.assertIsNone(flow.take_tokens())
        self.assertEqual(flow.pending_save(request.key), rotated)
        self.assertIsNone(flow.pending_save(('wrong', 1)))
        self.assertFalse(flow.saved(('wrong', 1), True))
        self.assertEqual(flow.state, 'awaiting_save')
        self.assertTrue(flow.saved(request.key, True))
        self.assertEqual(flow.state, 'ready')
        self.assertEqual(flow.take_tokens(), rotated)
        self.assertIsNone(flow.take_tokens())
        self.assertFalse(flow.saved(request.key, True))
        self.assertFalse(flow.receive(request.key, 200, rotated))

    def test_failed_save_never_restores_retired_pair_or_retries_refresh(self):
        for acknowledgement in (False, None, 1, 'yes'):
            with self.subTest(acknowledgement=acknowledgement):
                flow = RefreshFlow(Clock(), token())
                request = flow.start('SYNTHETIC-CLIENT')
                rotated = dict(token(), access_token='SYNTHETIC-ROTATED', refresh_token='SYNTHETIC-ROTATED-REFRESH')
                flow.receive(request.key, 200, rotated)
                self.assertTrue(flow.saved(request.key, acknowledgement))
                self.assertEqual(flow.state, 'reauth_required')
                self.assertIsNone(flow.take_tokens())
                self.assertIsNone(flow.pending_save(request.key))
                self.assertIsNone(flow.start('SYNTHETIC-CLIENT'))
                self.assertFalse(flow.saved(request.key, True))
                self.assertIsNone(flow._old)
                self.assertIsNone(flow._candidate)

    def test_cancel_at_network_or_save_phase_rejects_late_reply_and_ack(self):
        for after_reply in (False, True):
            with self.subTest(after_reply=after_reply):
                flow = RefreshFlow(Clock(), token())
                request = flow.start('SYNTHETIC-CLIENT')
                if after_reply:
                    flow.receive(request.key, 200, token())
                flow.cancel()
                flow.cancel()
                self.assertEqual(flow.state, 'reauth_required')
                self.assertFalse(flow.receive(request.key, 200, token()))
                self.assertFalse(flow.saved(request.key, True))
                self.assertIsNone(flow.pending_save(request.key))
                self.assertIsNone(flow.take_tokens())
                self.assertIsNone(flow.start('SYNTHETIC-CLIENT'))
                self.assertIsNone(flow._candidate)
                self.assertIsNone(flow._old)

    def test_timeout_or_expired_candidate_rejects_late_ack(self):
        for after_reply in (False, True):
            clock = Clock()
            flow = RefreshFlow(clock, token())
            request = flow.start('SYNTHETIC-CLIENT')
            if after_reply:
                clock.advance(2)
                flow.receive(request.key, 200, token())
            clock.advance(30)
            self.assertIsNone(flow.pending_save(request.key))
            self.assertFalse(flow.receive(request.key, 200, token()))
            self.assertFalse(flow.saved(request.key, True))
            self.assertIsNone(flow.take_tokens())
            self.assertEqual(flow.state, 'reauth_required')

    def test_malformed_or_error_responses_never_become_save_candidates(self):
        for status, body in [(500, token()), (True, token()), (200, None), (200, []),
                             (200, {}), (200, dict(token(), error='bad')),
                             (200, dict(token(), access_token='X\r\nBad')),
                             (200, dict(token(), token_type='basic')),
                             (200, dict(token(), expires_in=True)),
                             (200, dict(token(), refresh_token_expires_in=0))]:
            with self.subTest(status=status, body_type=type(body).__name__):
                flow = RefreshFlow(Clock(), token())
                request = flow.start('SYNTHETIC-CLIENT')
                self.assertTrue(flow.receive(request.key, status, body))
                self.assertEqual(flow.state, 'reauth_required')
                self.assertIsNone(flow.pending_save(request.key))
                self.assertIsNone(flow.take_tokens())

    def test_other_flow_key_cannot_authorize_this_flow(self):
        first = RefreshFlow(Clock(), token())
        second = RefreshFlow(Clock(), token())
        old = first.start('SYNTHETIC-CLIENT')
        new = second.start('SYNTHETIC-CLIENT')
        self.assertNotEqual(old.key, new.key)
        self.assertFalse(second.receive(old.key, 200, token()))
        self.assertEqual(second.state, 'refreshing')
        self.assertTrue(second.receive(new.key, 200, token()))

    def test_expired_ready_pair_cannot_be_taken(self):
        clock = Clock()
        flow = RefreshFlow(clock, token())
        request = flow.start('SYNTHETIC-CLIENT')
        flow.receive(request.key, 200, dict(token(), expires_in=2))
        self.assertTrue(flow.saved(request.key, True))
        clock.advance(2)
        self.assertIsNone(flow.take_tokens())
        self.assertEqual(flow.state, 'reauth_required')

    def test_invalid_initial_pair_or_client_never_produces_request(self):
        for pair, client in [(None, 'SYNTHETIC-CLIENT'), ({}, 'SYNTHETIC-CLIENT'),
                             (dict(token(), refresh_token=''), 'SYNTHETIC-CLIENT'),
                             (token(), None), (token(), 'bad\r\nclient')]:
            flow = RefreshFlow(Clock(), pair)
            self.assertIsNone(flow.start(client))
            self.assertEqual(flow.state, 'reauth_required')
            self.assertIsNone(flow.take_tokens())

    def test_response_latency_never_extends_candidate_lifetime(self):
        clock = Clock()
        flow = RefreshFlow(clock, token())
        request = flow.start('SYNTHETIC-CLIENT')
        clock.advance(3)
        self.assertTrue(flow.receive(request.key, 200, dict(token(), expires_in=2)))
        self.assertIsNone(flow.pending_save(request.key))
        self.assertFalse(flow.saved(request.key, True))
        self.assertEqual(flow.state, 'reauth_required')

    def test_candidate_is_allowlisted_copied_and_not_in_repr_or_output(self):
        import contextlib
        import io
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            flow = RefreshFlow(Clock(), token())
            request = flow.start('SYNTHETIC-CLIENT')
            body = dict(token(), extra='SYNTHETIC-UNRELATED-SECRET')
            flow.receive(request.key, 200, body)
            candidate = flow.pending_save(request.key)
            self.assertEqual(candidate, token())
            body['refresh_token'] = 'SYNTHETIC-MUTATED-BODY'
            candidate['access_token'] = 'SYNTHETIC-MUTATED-COPY'
            self.assertEqual(flow.pending_save(request.key), token())
            representation = repr(flow) + repr(request)
            for marker in ('SYNTHETIC', token()['access_token'], token()['refresh_token']):
                self.assertNotIn(marker, representation)
            flow.saved(request.key, True)
            self.assertEqual(flow.take_tokens(), token())
        self.assertEqual(stdout.getvalue() + stderr.getvalue(), '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
