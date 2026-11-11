"""Native connection-dialog lifecycle checks; synthetic scratch profile only."""

import json

import os

from pathlib import Path

import sys





def main():

    root = Path(os.environ['AGGIS_CONNECTION_SCRATCH']).resolve()

    assert root.is_relative_to(Path('C:/Users/Michael/AppData/Local/hermes/cache/scratch').resolve())

    assert (root / 'SYNTHETIC-ONLY').read_text() == 'connection-v1'

    plugin = Path(os.environ['AGGIS_CONNECTION_PLUGIN']).resolve()

    os.environ['QT_QPA_PLATFORM'] = 'offscreen'

    os.environ['QGIS_CUSTOM_CONFIG_PATH'] = str(root / 'profile')

    os.environ['QGIS_AUTH_DB_DIR_PATH'] = str(root / 'auth')

    (root / 'auth').mkdir()

    pass  # QGIS not available, skip this test

except ImportError:

            from qgis.PyQt.QtWidgets import QMainWindow

            # Delete only the actual test-owned main window to exercise teardown.

            started.clear(); release.clear(); delivered.clear()

            mode[0] = 'parent'

            results['dialog_close_drops_session_and_reopens_fresh'] = True

            assert connection.closed and connection.dialog is None

            connection.close()

            assert connection.dialog is dialog and dialog.connect_button.isEnabled()

            connection.open()

            assert not connection.timer.isActive()

            assert reopened_flow.state == 'cancelled' and not dialog.user_code.text()

            dialog.close()

            reopened_flow = connection.flow

            spin(lambda: connection.flow.state == 'waiting')

            dialog.connect_button.click()

            mode[0] = 'success'

            results['ui_cancel_aborts_late_native_reply'] = True

            assert cancelled_flow.access_token() is None

            assert not cancelled_flow.receive(stale_key, 200, {'access_token': access, 'token_type': 'bearer', 'expires_in': 30})

            spin(lambda: not transport.in_flight)

            spin(delivered.is_set)

            release.set()

            assert not connection.timer.isActive() and not dialog.user_code.text()

            assert not transport.in_flight and transport._closed

            assert cancelled_flow.access_token() is None and cancelled_flow.state == 'cancelled'

            dialog.cancel_button.click()

            stale_key = cancelled_flow.active

            transport = transports[-1]

            cancelled_flow = connection.flow

            spin(started.is_set)

            mode[0] = 'cancel'

            spin(lambda: connection.flow.state == 'waiting')

            dialog.connect_button.click()

            results['timer_expiry_drops_access'] = True

            assert dialog.connect_button.isEnabled() and not dialog.user_code.text()

            assert flow.access_token() is None and not connection.timer.isActive()

            spin(lambda: flow.state == 'expired')

            results['ui_producer_native_server_consumer'] = True

            assert posted[1][1]['device_code'] == [device]

            assert posted[0][1] == {'client_id': ['SYNTHETIC-CLIENT'], 'scope': ['offline_access']}

            assert not dialog.user_code.text() and 'session' in dialog.status.text().lower()

            assert 'SYNTHETIC-UNRETAINED-REFRESH' not in repr(vars(flow))

            assert flow.access_token() == access and flow.take_tokens() is None

            flow = connection.flow

            spin(lambda: connection.flow.state == 'authorized')

            assert len(posted) == 1 and not connection.start(), 'duplicate start sent a second request'

            assert not dialog.connect_button.isEnabled() and dialog.cancel_button.isEnabled()

            assert dialog.user_code.text() == 'ABCD-EFGH'

            spin(lambda: connection.flow.state == 'waiting')

            dialog.connect_button.click()

            assert dialog.connect_button.isEnabled()

            dialog = connection.dialog

            connection.open()

            connection = module.GitHubConnection(window, _fixture_factory=fixture)

        try:

        connection = None

    

            assert predicate(), 'connection event-loop deadline exceeded'

                time.sleep(.005)

                app.processEvents(QEventLoop.AllEvents, 20)

            while not predicate() and time.monotonic() < until:

            until = time.monotonic() + limit

        def spin(predicate, limit=4):

    

            return 'SYNTHETIC-CLIENT', transport

            transports.append(transport)

            transport = LoopbackTransport(parent)

        def fixture(parent):

        transports = []

    

                return 'http://127.0.0.1:' + str(server.server_port) + '/' + endpoint

            def _endpoint_url(self, endpoint):

        class LoopbackTransport(GitHubDeviceTransport):

    

        worker.start()

        worker = threading.Thread(target=server.serve_forever, daemon=True)

        server.daemon_threads = True

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)

    

                        delivered.set()

                    if request_mode in ('cancel', 'parent', 'quit'):

                finally:

                    pass

                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):

                    self.wfile.write(raw)

                    self.end_headers()

                    self.send_header('Content-Length', str(len(raw)))

                    self.send_response(200)

                try:

                raw = json.dumps(response).encode()

                                'refresh_token': 'SYNTHETIC-UNRETAINED-REFRESH'}

                    response = {'access_token': access, 'token_type': 'bearer', 'expires_in': 1,

                if self.path == '/token':

                            'interval': 1, 'expires_in': 10}

                            'verification_uri': 'https://github.com/login/device',

                response = {'device_code': device, 'user_code': 'ABCD-EFGH',

                    release.wait(4)

                    started.set()

                if request_mode in ('cancel', 'parent', 'quit'):

                request_mode = mode[0]

                posted.append((self.path, body))

                body = parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode('ascii'))

            def do_POST(self):

    

                pass

            def log_message(self, *args):

        class Handler(BaseHTTPRequestHandler):

    

        assert len(device) == 40

        device = 'SYNTHETIC-CONNECTION-DEVICE' + 'x' * 13

        access = 'SYNTHETIC-CONNECTION-ACCESS'

        started, release, delivered = (threading.Event() for _ in range(3))

        mode = ['success']

        posted = []

        assert Path(sys.modules['ag_tech_tooling.github_transport'].__file__).resolve() == plugin / 'github_transport.py'

        from ag_tech_tooling.github_transport import GitHubDeviceTransport

        from qgis.PyQt.QtCore import QEventLoop, QTimer, QObject, QCoreApplication, QEvent

        from urllib.parse import parse_qs

        import time

        import threading

        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    def exercise_session(module, app, window, plugin, seen, results):

    

    

            app.exitQgis()

            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

            window.close()

            signal.disconnect(observer)

            connection.close()

        finally:

            print('Default product connection gate and native dialog lifecycle passed')

            (root / 'assertions.json').write_text(json.dumps(results, indent=2))

            exercise_session(module, app, window, plugin, seen, results)

                       'provider_contacted': False, 'module_origin': str(plugin / 'github_connection.py')}

            results = {'default_gate_no_send': True, 'dialog_reopen_and_close': True,

            assert 'ag_tech_tooling.github_transport' not in sys.modules, 'Default product path instantiated network code'

            assert connection.dialog is None and not seen

            connection.open()

            assert connection.closed and connection.dialog is None and not dialog.isVisible()

            connection.close()

            connection.close()

            assert connection.dialog is dialog and not dialog.connect_button.isEnabled()

            connection.open()

            assert not dialog.isVisible()

            app.processEvents()

            dialog.close()

            assert connection.flow is None and not connection.timer.isActive() and not seen

            connection.start()  # Programmatic invocation cannot bypass the UI gate.

            assert 'offline' in dialog.notice.text().lower()

            assert 'unavailable' in dialog.status.text().lower()

            assert dialog.isVisible() and not dialog.connect_button.isEnabled()

            dialog = connection.dialog

            app.processEvents()

            connection.open()

        try:

        connection = module.GitHubConnection(window)

        window.show()

        window = QMainWindow()

        signal.connect(observer)

        observer = lambda params: seen.append(params.request().url().host())

        signal = QgsNetworkAccessManager.instance().requestAboutToBeCreated[QgsNetworkRequestParameters]

        seen = []

        assert 'auth_flow_model' not in sys.modules, 'Production UI must use its packaged session producer'

        assert Path(sys.modules['ag_tech_tooling.github_session'].__file__).resolve() == plugin / 'github_session.py'

        assert Path(module.__file__).resolve() == plugin / 'github_connection.py'

        from ag_tech_tooling import github_connection as module

        assert (plugin / 'github_connection.py').is_file(), 'Packaged production connection controller is missing'

        import ag_tech_tooling

        sys.path.insert(0, str(plugin.parent))

        assert Path(QSettings().fileName()).resolve().is_relative_to(root)

        assert Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(root)

        app.setQuitOnLastWindowClosed(False)

        app.initQgis()

        app = QgsApplication([], True)

            QSettings.setPath(QSettings.IniFormat, scope, str(root / 'settings'))

        for scope in (QSettings.UserScope, QSettings.SystemScope):

        QSettings.setDefaultFormat(QSettings.IniFormat)

        from qgis.core import QgsApplication, QgsNetworkAccessManager, QgsNetworkRequestParameters

        from qgis.PyQt.QtWidgets import QMainWindow

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
            from qgis.PyQt.QtCore import QSettings, QEvent, QCoreApplication
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

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


