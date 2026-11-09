"""Packaged access-only session regressions; synthetic values, no network/Qt."""
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT', str(Path(__file__).resolve().parents[1] / 'plugins')))
import auth_session_model_test as candidate_tests
from auth_flow_model_test import Clock, grant, token

try:
    from ag_tech_tooling import github_session as production
except ImportError:
    production = None


class PackagedSessionTest(candidate_tests.SessionOnlyTest):
    def candidate(self, clock):
        self.assertIsNotNone(production, 'Packaged session producer is missing')
        return production.SessionDeviceFlow(clock)

    def test_review_code_retained_only_while_waiting(self):
        for terminal in ('cancel', 'expiry', 'authorize', 'restart', 'failure'):
            with self.subTest(terminal=terminal):
                clock = Clock()
                flow = self.candidate(clock)
                first = flow.start('SYNTHETIC-CLIENT')
                flow.receive(first.key, 200, grant())
                self.assertEqual(flow.user_code, grant()['user_code'])
                self.assertEqual(flow.verification_uri, 'https://github.com/login/device')
                if terminal == 'cancel':
                    flow.cancel()
                elif terminal == 'restart':
                    flow.start('SYNTHETIC-CLIENT')
                elif terminal == 'expiry':
                    clock.advance(1000)
                    flow.tick()
                else:
                    clock.advance(5)
                    request = flow.poll()
                    flow.receive(request.key, 200, token() if terminal == 'authorize' else {})
                self.assertIsNone(flow.user_code)
                self.assertIsNone(flow.verification_uri)


if __name__ == '__main__':
    unittest.main(verbosity=2)
