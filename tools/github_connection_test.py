"""Native connection-dialog lifecycle checks; synthetic scratch profile only."""
import json
import os
from pathlib import Path
import sys


def main():
    root = Path(os.environ['AGGIS_CONNECTION_SCRATCH']).resolve()
    assert root.is_relative_to(Path('C:/temp/AppData/Local/hermes/cache/scratch').resolve())
    assert (root / 'SYNTHETIC-ONLY').read_text() == 'connection-v1'
    plugin = Path(os.environ['AGGIS_CONNECTION_PLUGIN']).resolve()
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    os.environ['QGIS_CUSTOM_CONFIG_PATH'] = str(root / 'profile')
    os.environ['QGIS_AUTH_DB_DIR_PATH'] = str(root / 'auth')
    (root / 'auth').mkdir()
    from qgis.PyQt.QtCore import QSettings, QEvent, QCoreApplication
    from qgis.PyQt.QtWidgets import QMainWindow
    from qgis.core import QgsApplication, QgsNetworkAccessManager, QgsNetworkRequestParameters
    QSettings.setDefaultFormat(QSettings.IniFormat)
    for scope in (QSettings.UserScope, QSettings.SystemScope):
        QSettings.setPath(QSettings.IniFormat, scope, str(root / 'settings'))
    app = QgsApplication([], True)
    app.initQgis()
    app.setQuitOnLastWindowClosed(False)
    assert Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(root)
    assert Path(QSettings().fileName()).resolve().is_relative_to(root)
    sys.path.insert(0, str(plugin.parent))
    import ag_tech_tooling
    assert (plugin / 'github_connection.py').is_file(), 'Packaged production connection controller is missing'
    from ag_tech_tooling import github_connection as module
    assert Path(module.__file__).resolve() == plugin / 'github_connection.py'
    assert Path(sys.modules['ag_tech_tooling.github_session'].__file__).resolve() == plugin / 'github_session.py'
    assert 'auth_flow_model' not in sys.modules, 'Production UI must use its packaged session producer'
    seen = []
    signal = QgsNetworkAccessManager.instance().requestAboutToBeCreated[QgsNetworkRequestParameters]
    observer = lambda params: seen.append(params.request().url().host())
    signal.connect(observer)
    window = QMainWindow()
    window.show()
    connection = module.GitHubConnection(window)
    try:
        connection.open()
        app.processEvents()
        dialog = connection.dialog
        assert dialog.isVisible() and not dialog.connect_button.isEnabled()
        assert 'unavailable' in dialog.status.text().lower()
        assert 'offline' in dialog.notice.text().lower()
        connection.start()  # Programmatic invocation cannot bypass the UI gate.
        assert connection.flow is None and not connection.timer.isActive() and not seen
        dialog.close()
        app.processEvents()
        assert not dialog.isVisible()
        connection.open()
        assert connection.dialog is dialog and not dialog.connect_button.isEnabled()
        connection.close()
        connection.close()
        assert connection.closed and connection.dialog is None and not dialog.isVisible()
        connection.open()
        assert connection.dialog is None and not seen
        assert 'ag_tech_tooling.github_transport' not in sys.modules, 'Default product path instantiated network code'
        results = {'default_gate_no_send': True, 'dialog_reopen_and_close': True,
                   'provider_contacted': False, 'module_origin': str(plugin / 'github_connection.py')}
        exercise_session(module, app, window, plugin, seen, results)
        (root / 'assertions.json').write_text(json.dumps(results, indent=2))
        print('Default product connection gate and native dialog lifecycle passed')
    finally:
        connection.close()
        signal.disconnect(observer)
        window.close()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        app.exitQgis()


def exercise_session(module, app, window, plugin, seen, results):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    import time
    from urllib.parse import parse_qs
    from qgis.PyQt.QtCore import QEventLoop, QTimer, QObject, QCoreApplication, QEvent
    from ag_tech_tooling.github_transport import GitHubDeviceTransport
    assert Path(sys.modules['ag_tech_tooling.github_transport'].__file__).resolve() == plugin / 'github_transport.py'
    posted = []
    mode = ['success']
    started, release, delivered = (threading.Event() for _ in range(3))
    access = 'SYNTHETIC-CONNECTION-ACCESS'
    device = 'SYNTHETIC-CONNECTION-DEVICE' + 'x' * 13
    assert len(device) == 40

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode('ascii'))
            posted.append((self.path, body))
            request_mode = mode[0]
            if request_mode in ('cancel', 'parent', 'quit'):
                started.set()
                release.wait(4)
            response = {'device_code': device, 'user_code': 'ABCD-EFGH',
                        'verification_uri': 'https://github.com/login/device',
                        'interval': 1, 'expires_in': 10}
            if self.path == '/token':
                response = {'access_token': access, 'token_type': 'bearer', 'expires_in': 1,
                            'refresh_token': 'SYNTHETIC-UNRETAINED-REFRESH'}
            raw = json.dumps(response).encode()
            try:
                self.send_response(200)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            finally:
                if request_mode in ('cancel', 'parent', 'quit'):
                    delivered.set()

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()

    class LoopbackTransport(GitHubDeviceTransport):
        def _endpoint_url(self, endpoint):
            return 'http://127.0.0.1:' + str(server.server_port) + '/' + endpoint

    transports = []
    def fixture(parent):
        transport = LoopbackTransport(parent)
        transports.append(transport)
        return 'SYNTHETIC-CLIENT', transport

    def spin(predicate, limit=4):
        until = time.monotonic() + limit
        while not predicate() and time.monotonic() < until:
            app.processEvents(QEventLoop.AllEvents, 20)
            time.sleep(.005)
        assert predicate(), 'connection event-loop deadline exceeded'

    connection = None
    try:
        connection = module.GitHubConnection(window, _fixture_factory=fixture)
        connection.open()
        dialog = connection.dialog
        assert dialog.connect_button.isEnabled()
        dialog.connect_button.click()
        spin(lambda: connection.flow.state == 'waiting')
        assert dialog.user_code.text() == 'ABCD-EFGH'
        assert not dialog.connect_button.isEnabled() and dialog.cancel_button.isEnabled()
        assert len(posted) == 1 and not connection.start(), 'duplicate start sent a second request'
        spin(lambda: connection.flow.state == 'authorized')
        flow = connection.flow
        assert flow.access_token() == access and flow.take_tokens() is None
        assert 'SYNTHETIC-UNRETAINED-REFRESH' not in repr(vars(flow))
        assert not dialog.user_code.text() and 'session' in dialog.status.text().lower()
        assert posted[0][1] == {'client_id': ['SYNTHETIC-CLIENT'], 'scope': ['offline_access']}
        assert posted[1][1]['device_code'] == [device]
        results['ui_producer_native_server_consumer'] = True
        spin(lambda: flow.state == 'expired')
        assert flow.access_token() is None and not connection.timer.isActive()
        assert dialog.connect_button.isEnabled() and not dialog.user_code.text()
        results['timer_expiry_drops_access'] = True
        dialog.connect_button.click()
        spin(lambda: connection.flow.state == 'waiting')
        mode[0] = 'cancel'
        spin(started.is_set)
        cancelled_flow = connection.flow
        transport = transports[-1]
        stale_key = cancelled_flow.active
        dialog.cancel_button.click()
        assert cancelled_flow.access_token() is None and cancelled_flow.state == 'cancelled'
        assert not transport.in_flight and transport._closed
        assert not connection.timer.isActive() and not dialog.user_code.text()
        release.set()
        spin(delivered.is_set)
        spin(lambda: not transport.in_flight)
        assert not cancelled_flow.receive(stale_key, 200, {'access_token': access, 'token_type': 'bearer', 'expires_in': 30})
        assert cancelled_flow.access_token() is None
        results['ui_cancel_aborts_late_native_reply'] = True
        mode[0] = 'success'
        dialog.connect_button.click()
        spin(lambda: connection.flow.state == 'waiting')
        reopened_flow = connection.flow
        dialog.close()
        assert reopened_flow.state == 'cancelled' and not dialog.user_code.text()
        assert not connection.timer.isActive()
        connection.open()
        assert connection.dialog is dialog and dialog.connect_button.isEnabled()
        connection.close()
        assert connection.closed and connection.dialog is None
        results['dialog_close_drops_session_and_reopens_fresh'] = True
        mode[0] = 'parent'
        started.clear(); release.clear(); delivered.clear()
        # Delete only the actual test-owned main window to exercise teardown.
        from qgis.PyQt.QtWidgets import QMainWindow
        parent_window = QMainWindow()
        connection = module.GitHubConnection(parent_window, _fixture_factory=fixture)
        connection.open()
        connection.dialog.connect_button.click()
        spin(started.is_set)
        flow = connection.flow
        transport = transports[-1]
        parent_window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        assert connection.closed and flow.state == 'cancelled' and transport._reply is None
        release.set(); spin(delivered.is_set)
        results['parent_destruction_clears_session'] = True
        connection = None
        mode[0] = 'quit'
        started.clear(); release.clear(); delivered.clear()
        connection = module.GitHubConnection(window, _fixture_factory=fixture)
        connection.open()
        connection.dialog.connect_button.click()
        flow = connection.flow
        transport = transports[-1]
        quit_poll = QTimer()
        quit_poll.timeout.connect(lambda: app.quit() if started.is_set() else None)
        quit_poll.start(5)
        guard = QTimer()
        guard.setSingleShot(True); guard.timeout.connect(app.quit); guard.start(3000)
        app.exec()
        quit_poll.stop(); guard.stop()
        assert started.is_set() and connection.closed and flow.state == 'cancelled'
        assert transport._closed and not transport.in_flight and not connection.timer.isActive()
        release.set(); spin(delivered.is_set)
        results['actual_quit_clears_controller_session'] = True
        assert all(host == '127.0.0.1' for host in seen)
        assert len(posted) == len(seen) == 7
        results['native_loopback_posts'] = len(posted)
    finally:
        release.set()
        if connection:
            connection.close()
        server.shutdown(); server.server_close(); worker.join(timeout=3)
        assert not worker.is_alive()


if __name__ == '__main__':
    main()
