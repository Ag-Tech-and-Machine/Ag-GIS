"""Actual Qt timer lifecycle, synthetic descriptions only; NOT native login/UI.

Run using the existing QGIS Python bootstrap with an explicit scratch output path.
No QgsApplication initialization, settings, auth store, network or product imports.
"""
import json
from pathlib import Path
import sys
import time

from qgis.PyQt.QtCore import QCoreApplication, QTimer

from auth_flow_model import SessionDeviceFlow
from auth_flow_model_test import grant, token


def main():
    output = Path(sys.argv[1]).resolve()
    base = Path('C:/temp/AppData/Local/hermes/cache/scratch').resolve()
    assert output.is_relative_to(base) and output.parent.name.startswith('aggis-session-')
    app = QCoreApplication([])
    result = {'synthetic_only': True, 'network': False, 'product_wired': False}
    errors = []
    flow = SessionDeviceFlow(time.monotonic)
    cancelled = SessionDeviceFlow(time.monotonic)
    at_quit = SessionDeviceFlow(time.monotonic)
    assert flow.state == 'idle' and flow.access_token() is None and flow.poll() is None
    result['fresh_requires_sign_in'] = True
    timers = []

    def guarded(callback):
        def run():
            try:
                callback()
            except Exception as exc:
                errors.append(type(exc).__name__)
                app.quit()
        return run

    def later(ms, callback):
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(guarded(callback))
        timers.append(timer)
        timer.start(ms)

    def seed(candidate):
        request = candidate.start('SYNTHETIC-CLIENT')
        body = dict(grant(), interval=1)
        assert candidate.receive(request.key, 200, body)

    def start():
        seed(flow)
        seed(cancelled)
        seed(at_quit)
        later(1200, poll_ready)

    def poll_ready():
        request = flow.poll()
        assert request is not None
        assert flow.receive(request.key, 200, dict(token(), expires_in=1))
        assert flow.access_token() == token()['access_token']
        assert flow._tokens is None and flow.take_tokens() is None
        assert token()['refresh_token'] not in repr(vars(flow))
        result['access_only'] = True
        delayed = cancelled.poll()
        assert delayed is not None
        cancelled.cancel()

        def delivered():
            assert not cancelled.receive(delayed.key, 200, token())
            assert cancelled.access_token() is None and cancelled._access is None
            result['late_qt_callback_refused'] = True

        later(0, delivered)
        request_quit = at_quit.poll()
        assert request_quit is not None
        assert at_quit.receive(request_quit.key, 200, token())
        assert at_quit.access_token() is not None
        later(1200, expired)

    def expired():
        # No periodic tick was delivered: the accessor itself must expire access.
        assert flow.access_token() is None and flow.state == 'expired'
        assert flow._access is None and flow.poll() is None
        result['real_monotonic_expiry'] = True
        app.quit()

    app.aboutToQuit.connect(at_quit.cancel)
    later(0, start)
    later(8000, lambda: (errors.append('watchdog'), app.quit()))
    app.exec()
    for timer in timers:
        timer.stop()
    assert not errors, 'Qt lifecycle assertion failed: ' + repr(errors)
    assert at_quit.state == 'cancelled' and at_quit._access is None
    assert at_quit.access_token() is None
    result['about_to_quit_clears_access'] = True
    expected = {'synthetic_only', 'network', 'product_wired', 'fresh_requires_sign_in',
                'access_only', 'late_qt_callback_refused', 'real_monotonic_expiry',
                'about_to_quit_clears_access'}
    assert set(result) == expected
    assert all(value is True for key, value in result.items() if key not in ('network', 'product_wired'))
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Qt session-only candidate: access/expiry/late-callback/quit assertions passed; no login/network.')


if __name__ == '__main__':
    main()
