"""Deterministic developer model tests. No OAuth, socket, Qt, or real credential."""
import unittest

from auth_flow_model import DeviceFlow


class Clock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def grant():
    return {'device_code': 'D' * 40, 'user_code': 'ABCD-EFGH',
            'verification_uri': 'https://github.com/login/device',
            'expires_in': 90, 'interval': 5}


def token():
    return {'access_token': 'SYNTHETIC-ACCESS-NOT-A-CREDENTIAL',
            'refresh_token': 'SYNTHETIC-REFRESH-NOT-A-CREDENTIAL',
            'token_type': 'bearer', 'expires_in': 30, 'refresh_token_expires_in': 60}


class DeviceFlowTest(unittest.TestCase):
    def test_pending_and_slow_down_never_overlap_or_poll_early(self):
        clock = Clock()
        flow = DeviceFlow(clock)
        request = flow.start('SYNTHETIC-CLIENT')
        self.assertEqual(request.endpoint, 'device')
        self.assertIsNone(flow.poll())
        flow.receive(request.key, 200, grant())
        self.assertEqual(flow.state, 'waiting')
        self.assertIsNone(flow.poll())
        clock.advance(5)
        poll = flow.poll()
        self.assertEqual(poll.endpoint, 'token')
        self.assertEqual(poll.payload['grant_type'], 'urn:ietf:params:oauth:grant-type:device_code')
        self.assertIsNone(flow.poll())
        flow.receive(poll.key, 200, {'error': 'authorization_pending'})
        clock.advance(4)
        self.assertIsNone(flow.poll())
        clock.advance(1)
        slow = flow.poll()
        flow.receive(slow.key, 200, {'error': 'slow_down', 'interval': 10})
        clock.advance(9)
        self.assertIsNone(flow.poll())
        clock.advance(1)
        later = flow.poll()
        flow.receive(later.key, 200, {'error': 'authorization_pending'})
        clock.advance(9)
        self.assertIsNone(flow.poll())
        clock.advance(1)
        success = flow.poll()
        flow.receive(success.key, 200, token())
        self.assertEqual(flow.state, 'authorized')
        self.assertEqual(flow.take_tokens()['access_token'], token()['access_token'])
        self.assertIsNone(flow.take_tokens())
        self.assertIsNone(flow.poll())

    def test_cancel_invalidates_inflight_and_old_generations(self):
        clock = Clock()
        flow = DeviceFlow(clock)
        first = flow.start('SYNTHETIC-CLIENT')
        flow.cancel()
        self.assertEqual(flow.state, 'cancelled')
        self.assertIsNone(flow.active)
        self.assertFalse(flow.receive(first.key, 200, grant()))
        second = flow.start('SYNTHETIC-CLIENT')
        self.assertFalse(flow.receive(first.key, 200, grant()))
        flow.receive(second.key, 200, grant())
        clock.advance(5)
        poll = flow.poll()
        flow.cancel()
        self.assertFalse(flow.receive(poll.key, 200, token()))
        self.assertIsNone(flow.take_tokens())
        self.assertIsNone(flow._device)
        self.assertIsNone(flow._client)
        self.assertIsNone(flow.poll())
        flow.cancel()  # close/unload is idempotent at the model boundary

    def test_expiry_refuses_due_polls_and_late_success(self):
        for late_reply in (False, True):
            with self.subTest(late_reply=late_reply):
                clock = Clock()
                flow = DeviceFlow(clock)
                first = flow.start('SYNTHETIC-CLIENT')
                flow.receive(first.key, 200, grant())
                clock.advance(5)
                poll = flow.poll() if late_reply else None
                clock.advance(85)
                if poll:
                    self.assertFalse(flow.receive(poll.key, 200, token()))
                else:
                    self.assertIsNone(flow.poll())
                self.assertEqual(flow.state, 'expired')
                self.assertIsNone(flow.active)
                self.assertIsNone(flow._device)
                self.assertIsNone(flow.take_tokens())

    def test_duplicate_reply_cannot_consume_new_poll(self):
        clock = Clock()
        flow = DeviceFlow(clock)
        first = flow.start('SYNTHETIC-CLIENT')
        flow.receive(first.key, 200, grant())
        clock.advance(5)
        poll = flow.poll()
        flow.receive(poll.key, 200, {'error': 'authorization_pending'})
        clock.advance(5)
        next_poll = flow.poll()
        self.assertFalse(flow.receive(poll.key, 200, token()))
        self.assertEqual(flow.active, next_poll.key)
        self.assertIsNone(flow.take_tokens())
        flow.receive(next_poll.key, 200, token())
        self.assertEqual(flow.state, 'authorized')

    def test_terminal_provider_errors_and_http_failures_never_authorize(self):
        for error in ('access_denied', 'expired_token', 'token_expired',
                      'device_flow_disabled', 'incorrect_client_credentials',
                      'incorrect_device_code', 'unsupported_grant_type',
                      'unrecognized-error-SYNTHETIC-SECRET'):
            with self.subTest(error=error):
                clock = Clock()
                flow = DeviceFlow(clock)
                first = flow.start('SYNTHETIC-CLIENT')
                flow.receive(first.key, 200, grant())
                clock.advance(5)
                poll = flow.poll()
                flow.receive(poll.key, 200, {'error': error, 'error_description': token()})
                expected = {'access_denied': 'denied', 'expired_token': 'expired',
                            'token_expired': 'expired'}.get(error, 'failed')
                self.assertEqual(flow.state, expected)
                self.assertIsNone(flow.take_tokens())
                self.assertIsNone(flow._device)
                self.assertIsNone(flow.poll())
        for status in (0, 301, 302, 400, 401, 429, 500, True):
            with self.subTest(status=status):
                flow = DeviceFlow(Clock())
                first = flow.start('SYNTHETIC-CLIENT')
                flow.receive(first.key, status, grant())
                self.assertEqual(flow.state, 'failed')

    def test_invalid_device_payloads_fail_closed_without_exceptions(self):
        invalid = [None, [], 'SYNTHETIC-SECRET', {},
                   dict(grant(), verification_uri='http://github.com/login/device'),
                   dict(grant(), verification_uri='https://github.com.evil.invalid/login/device'),
                   dict(grant(), verification_uri='https://github.com/login/device?leak=yes'),
                   dict(grant(), verification_uri='https://user@github.com/login/device'),
                   dict(grant(), interval=True), dict(grant(), interval=0),
                   dict(grant(), interval=-1), dict(grant(), interval='5'),
                   dict(grant(), expires_in=0), dict(grant(), expires_in=float('nan')),
                   dict(grant(), device_code='short'), dict(grant(), device_code='X' * 41),
                   dict(grant(), user_code='bad\r\ncode')]
        for body in invalid:
            with self.subTest(body=type(body).__name__):
                flow = DeviceFlow(Clock())
                request = flow.start('SYNTHETIC-CLIENT')
                flow.receive(request.key, 200, body)
                self.assertEqual(flow.state, 'failed')
                self.assertIsNone(flow.active)
                self.assertIsNone(flow._device)

    def test_invalid_token_payloads_and_error_success_mixtures_fail_closed(self):
        invalid = [None, [], {}, dict(token(), access_token=''),
                   dict(token(), access_token='X\r\nInjected: bad'),
                   dict(token(), token_type='basic'), dict(token(), expires_in=True),
                   dict(token(), expires_in=-1), dict(token(), refresh_token=''),
                   dict(token(), refresh_token_expires_in=0),
                   dict(token(), error='authorization_pending')]
        for body in invalid:
            with self.subTest(body=type(body).__name__):
                clock = Clock()
                flow = DeviceFlow(clock)
                request = flow.start('SYNTHETIC-CLIENT')
                flow.receive(request.key, 200, grant())
                clock.advance(5)
                poll = flow.poll()
                flow.receive(poll.key, 200, body)
                self.assertEqual(flow.state, 'failed')
                self.assertIsNone(flow.take_tokens())
                self.assertIsNone(flow._device)

    def test_request_timeout_and_no_configuration_stay_local(self):
        flow = DeviceFlow(Clock())
        self.assertIsNone(flow.start(None))
        self.assertEqual(flow.state, 'unconfigured')
        self.assertIsNone(flow.poll())
        clock = Clock()
        flow = DeviceFlow(clock)
        request = flow.start('SYNTHETIC-CLIENT')
        clock.advance(30)
        flow.tick()
        self.assertEqual(flow.state, 'failed')
        self.assertFalse(flow.receive(request.key, 200, grant()))
        self.assertIsNone(flow.active)
        clock = Clock()
        flow = DeviceFlow(clock)
        request = flow.start('SYNTHETIC-CLIENT')
        clock.advance(3)
        flow.receive(request.key, 200, grant())
        self.assertEqual(flow.deadline, 190)  # not extended by response latency
        clock.advance(5)
        poll = flow.poll()
        clock.advance(30)
        flow.tick()
        self.assertEqual(flow.state, 'failed')
        self.assertFalse(flow.receive(poll.key, 200, token()))
        self.assertIsNone(flow.take_tokens())

    def test_allowlisted_diagnostics_never_include_response_or_request_secrets(self):
        import contextlib
        import io
        import json
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            clock = Clock()
            flow = DeviceFlow(clock)
            request = flow.start('SYNTHETIC-CLIENT')
            flow.receive(request.key, 200, grant())
            clock.advance(5)
            poll = flow.poll()
            flow.receive(poll.key, 200, dict(token(), error_description='SYNTHETIC-PRIVATE-TEXT',
                         Authorization='Bearer SYNTHETIC-HEADER', extra={'secret': 'SYNTHETIC-NESTED'}))
            report = json.dumps(flow.diagnostics()) + repr(flow) + repr(request) + repr(poll)
            self.assertTrue(flow.diagnostics()['events'])
            self.assertEqual(flow.diagnostics()['state'], 'authorized')
            for secret in (grant()['device_code'], grant()['user_code'],
                           token()['access_token'], token()['refresh_token'],
                           'SYNTHETIC-PRIVATE-TEXT', 'SYNTHETIC-HEADER', 'SYNTHETIC-NESTED'):
                self.assertNotIn(secret, report + stdout.getvalue() + stderr.getvalue())
            captured = flow.take_tokens()
            self.assertEqual(set(captured), set(token()))
            flow.start('SYNTHETIC-CLIENT')
            self.assertIsNone(flow.take_tokens())
            self.assertNotIn('SYNTHETIC-CLIENT', json.dumps(flow.diagnostics()))
            flow.cancel()
            self.assertEqual(flow.diagnostics()['state'], 'cancelled')
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '')

    def test_provider_error_text_is_not_diagnostic_content(self):
        import json
        flow = DeviceFlow(Clock())
        request = flow.start('SYNTHETIC-CLIENT')
        flow.receive(request.key, 500, {'error': 'SYNTHETIC-PRIVATE-ERROR',
                                     'error_description': 'Bearer SYNTHETIC-HEADER'})
        diagnostic = json.dumps(flow.diagnostics())
        self.assertEqual(flow.state, 'failed')
        self.assertNotIn('SYNTHETIC', diagnostic)
        self.assertNotIn('Bearer', diagnostic)
        self.assertNotIn('error_description', diagnostic)

    def test_deterministic_transport_delayed_delivery_cannot_revive_cancelled_flow(self):
        from unittest.mock import patch
        # Descriptions/queued callbacks only, NOT native Qt or provider networking.
        clock = Clock()
        flow = DeviceFlow(clock)
        queue = []
        with patch('socket.socket', side_effect=AssertionError('No networking permitted')) as socket:
            request = flow.start('SYNTHETIC-CLIENT')
            queue.append((request.key, 200, grant()))
            flow.receive(*queue.pop(0))
            clock.advance(5)
            poll = flow.poll()
            queue.append((poll.key, 200, token()))
            flow.cancel()
            self.assertFalse(flow.receive(*queue.pop(0)))
            self.assertEqual(flow.state, 'cancelled')
            self.assertIsNone(flow.take_tokens())
            socket.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
