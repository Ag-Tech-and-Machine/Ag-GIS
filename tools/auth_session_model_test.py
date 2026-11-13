"""Synthetic session-only candidate checks; no product/login or protected storage."""
import unittest

import auth_flow_model as model
from auth_flow_model_test import Clock, grant, token


class SessionOnlyTest(unittest.TestCase):
    def candidate(self, clock):
        candidate = getattr(model, 'SessionDeviceFlow', None)
        if candidate is None:
            self.fail('Session-only candidate is not implemented')
        return candidate(clock)

    def authorized(self, clock, response=None):
        flow = self.candidate(clock)
        first = flow.start('SYNTHETIC-CLIENT')
        flow.receive(first.key, 200, grant())
        clock.advance(5)
        poll = flow.poll()
        flow.receive(poll.key, 200, token() if response is None else response)
        return flow

    def test_access_only_never_releases_or_retains_refresh_pair(self):
        clock = Clock()
        response = dict(token(), extra='SYNTHETIC-PRIVATE')
        flow = self.authorized(clock, response)
        self.assertEqual(flow.state, 'authorized')
        self.assertEqual(flow.access_token(), token()['access_token'])
        self.assertEqual(flow.access_token(), token()['access_token'])
        self.assertIsNone(flow.take_tokens(), 'Inherited pair API must stay disabled')
        self.assertIsNone(flow._tokens)
        self.assertNotIn(token()['refresh_token'], repr(vars(flow)))
        self.assertNotIn('SYNTHETIC-PRIVATE', repr(vars(flow)))
        self.assertEqual(response['refresh_token'], token()['refresh_token'],
                         'Caller response ownership is unchanged; no secure erasure claim')
        self.assertIsNone(flow.poll())

    def test_expiry_and_cancel_drop_access_and_require_fresh_sign_in(self):
        for action in ('cancel', 'expiry', 'restart'):
            with self.subTest(action=action):
                clock = Clock()
                flow = self.authorized(clock)
                if action == 'cancel':
                    flow.cancel()
                elif action == 'expiry':
                    clock.advance(30)
                    flow.tick()
                else:
                    flow.start('SYNTHETIC-CLIENT')
                self.assertIsNone(flow.access_token())
                self.assertIsNone(flow._access, 'Terminal/start must release its access reference')
                self.assertIsNone(flow.take_tokens())
        clock = Clock()
        flow = self.authorized(clock)
        clock.advance(30)
        self.assertIsNone(flow.access_token(), 'Token access must check expiry without a timer')
        self.assertEqual(flow.state, 'expired')
        self.assertIsNone(flow.poll())
        fresh = self.candidate(clock)
        self.assertIsNone(fresh.access_token())
        self.assertIsNone(fresh.poll(), 'New process/session has no resume path')

    def test_lifetime_starts_at_poll_send_not_response_or_first_use(self):
        clock = Clock()
        flow = self.candidate(clock)
        first = flow.start('SYNTHETIC-CLIENT')
        flow.receive(first.key, 200, grant())
        clock.advance(5)
        poll = flow.poll()
        clock.advance(10)
        flow.receive(poll.key, 200, dict(token(), expires_in=12))
        self.assertEqual(flow.access_token(), token()['access_token'])
        clock.advance(2)
        self.assertIsNone(flow.access_token())
        self.assertEqual(flow.state, 'expired')
        flow.cancel()
        self.assertFalse(flow.receive(poll.key, 200, token()))
        self.assertIsNone(flow._access)

    def test_invalid_access_and_error_success_mixtures_fail_closed(self):
        for response in ({}, dict(token(), access_token=''),
                         dict(token(), token_type='basic'),
                         dict(token(), expires_in=True), dict(token(), expires_in=0),
                         dict(token(), error='authorization_pending')):
            with self.subTest(keys=sorted(response)):
                flow = self.authorized(Clock(), response)
                self.assertEqual(flow.state, 'failed')
                self.assertIsNone(flow.access_token())
                self.assertIsNone(flow._access)
                self.assertIsNone(flow.take_tokens())

    def test_access_only_does_not_require_refresh_credentials(self):
        response = {'access_token': token()['access_token'],
                    'token_type': 'bearer', 'expires_in': 30}
        flow = self.authorized(Clock(), response)
        self.assertEqual(flow.access_token(), response['access_token'])
        self.assertIsNone(flow.take_tokens())
        for secret in (response['access_token'], grant()['device_code'], grant()['user_code']):
            self.assertNotIn(secret, repr(flow.diagnostics()) + repr(flow))

    def test_cancelled_old_generation_cannot_reauthorize_new_session(self):
        clock = Clock()
        flow = self.candidate(clock)
        first = flow.start('SYNTHETIC-CLIENT')
        flow.receive(first.key, 200, grant())
        clock.advance(5)
        poll = flow.poll()
        flow.cancel()
        new = flow.start('SYNTHETIC-CLIENT')
        self.assertFalse(flow.receive(poll.key, 200, token()))
        self.assertEqual(flow.active, new.key)
        self.assertIsNone(flow.access_token())
        self.assertIsNone(flow._access)


if __name__ == '__main__':
    unittest.main(verbosity=2)
