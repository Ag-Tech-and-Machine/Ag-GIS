"""Real loopback tests of the packaged transport; no provider or real credentials.

Run through run_github_transport_test.py. Only the test subclass replaces fixed
HTTPS endpoints with test-owned loopback. It is NOT a configurable product host.
"""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
import ssl
import sys
import threading
import time
from urllib.parse import parse_qs


def main():
    root = Path(os.environ['AGGIS_TRANSPORT_SCRATCH']).resolve()
    base = Path('C:/Users/Michael/AppData/Local/hermes/cache/scratch').resolve()
    assert root.is_relative_to(base) and root.name.startswith('aggis-transport-')
    assert (root / 'SYNTHETIC-ONLY').read_text() == 'transport-v1'
    plugin = Path(os.environ['AGGIS_TRANSPORT_PLUGIN']).resolve()
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    os.environ['QGIS_CUSTOM_CONFIG_PATH'] = str(root / 'profile')
    os.environ['QGIS_AUTH_DB_DIR_PATH'] = str(root / 'auth')
    (root / 'auth').mkdir()
    from qgis.PyQt.QtCore import QObject, QSettings, QEventLoop, QTimer, QCoreApplication, QEvent
    from qgis.core import QgsApplication, QgsNetworkAccessManager, QgsNetworkRequestParameters
    QSettings.setDefaultFormat(QSettings.IniFormat)
    for scope in (QSettings.UserScope, QSettings.SystemScope):
        QSettings.setPath(QSettings.IniFormat, scope, str(root / 'settings'))
    app = QgsApplication([], False)
    app.initQgis()
    assert Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(root)
    assert Path(QSettings().fileName()).resolve().is_relative_to(root)
    assert (plugin / 'github_transport.py').is_file(), 'packaged native transport is missing'
    spec = importlib.util.spec_from_file_location('tested_transport', plugin / 'github_transport.py')
    assert spec is not None and spec.loader is not None, 'packaged native transport is missing'
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert Path(module.__file__).resolve() == plugin / 'github_transport.py'
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from auth_flow_model import SessionDeviceFlow, Request
    manager = QgsNetworkAccessManager.instance()
    original_timeout = manager.timeout()
    mode = ['success']
    posted = []
    seen = []
    logged = []
    late_started, late_release, late_done = (threading.Event() for _ in range(3))
    marker = 'SYNTHETIC-TRANSPORT-ACCESS'
    device_marker = 'SYNTHETIC-DEVICE-CODE-' + 'd' * 18
    assert len(device_marker) == 40
    markers = (marker, device_marker, 'ABCD-EFGH', 'SYNTHETIC-DO-NOT-RETAIN')
    results = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            raw = self.rfile.read(int(self.headers['Content-Length']))
            payload = parse_qs(raw.decode('ascii'))
            posted.append((mode[0], self.path, payload))
            if mode[0] in ('cancel', 'timeout', 'quit', 'parent'):
                late_started.set()
                late_release.wait(4)
            body = {'device_code': device_marker, 'user_code': 'ABCD-EFGH',
                    'verification_uri': 'https://github.com/login/device',
                    'interval': 1, 'expires_in': 20}
            if self.path == '/token':
                body = {'access_token': marker, 'token_type': 'bearer', 'expires_in': 20,
                        'refresh_token': 'SYNTHETIC-DO-NOT-RETAIN', 'error_description': marker}
            data = json.dumps(body).encode()
            if mode[0] == 'oversize':
                data = json.dumps(dict(body, ignored='x' * 70000)).encode()
            elif mode[0] == 'duplicate':
                data = b'{"access_token":"one","access_token":"two","token_type":"bearer","expires_in":20}'
            elif mode[0] == 'mixed':
                data = b'{"error":"authorization_pending","refresh_token":"do-not-ignore-this-mixture"}'
            try:
                self.send_response(307 if mode[0] == 'redirect' else 200)
                if mode[0] == 'redirect':
                    self.send_header('Location', 'http://127.0.0.1:' + str(self.server.server_port) + '/sink')
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            finally:
                if mode[0] in ('cancel', 'timeout', 'quit', 'parent'):
                    late_done.set()

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    tls_server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    tls_server.daemon_threads = True
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls_context.load_cert_chain(root / 'cert.pem', root / 'key.pem')
    tls_server.socket = tls_context.wrap_socket(tls_server.socket, server_side=True)
    tls_thread = threading.Thread(target=tls_server.serve_forever, daemon=True)
    tls_thread.start()
    class LoopbackTransport(module.GitHubDeviceTransport):
        def _endpoint_url(self, endpoint):
            return 'http://127.0.0.1:' + str(server.server_port) + '/' + endpoint

    def spin(predicate, limit=4):
        until = time.monotonic() + limit
        while not predicate() and time.monotonic() < until:
            app.processEvents(QEventLoop.AllEvents, 20)
            time.sleep(.005)
        assert predicate(), 'native event-loop deadline exceeded'

    def observe(params):
        req = params.request()
        seen.append((req.url().host(), bytes(req.rawHeader(b'Authorization')),
                     bytes(params.content())))
    def log(message, tag, level):
        if any(value in message or value in tag for value in markers):
            logged.append(True)
    signal = manager.requestAboutToBeCreated[QgsNetworkRequestParameters]
    signal.connect(observe)
    QgsApplication.messageLog().messageReceived.connect(log)
    transport = None
    try:
        assert module.GitHubDeviceTransport._endpoint_url(None, 'device') == 'https://github.com/login/device/code'
        assert module.GitHubDeviceTransport._endpoint_url(None, 'token') == 'https://github.com/login/oauth/access_token'
        transport = LoopbackTransport()
        flow = SessionDeviceFlow(time.monotonic)
        received = []
        def receive(key, status, body):
            received.append(set(body))
            assert 'refresh_token' not in body and 'error_description' not in body
            flow.receive(key, status, body)
        assert transport.send(flow.start('synthetic-client'), receive)
        assert not transport.send(Request((999, 1), 'device', {'client_id': 'other', 'scope': 'offline_access'}), receive)
        spin(lambda: flow.state == 'waiting')
        spin(lambda: time.monotonic() >= flow.next_poll)
        assert transport.send(flow.poll(), receive)
        spin(lambda: flow.state == 'authorized')
        assert flow.access_token() == marker and flow.take_tokens() is None
        assert posted[0][2] == {'client_id': ['synthetic-client'], 'scope': ['offline_access']}
        assert posted[1][2]['device_code'] == [device_marker]
        assert len(received) == 2
        results['model_native_success'] = True
        flow.cancel()
        transport.close()
        assert not transport.send(Request((9, 1), 'device', {'client_id': 'x', 'scope': 'offline_access'}), receive)
        mode[0] = 'cancel'
        transport = LoopbackTransport()
        flow = SessionDeviceFlow(time.monotonic)
        callbacks = []
        assert transport.send(flow.start('synthetic-client'), lambda *args: callbacks.append(True))
        spin(late_started.is_set)
        transport.cancel()
        flow.cancel()
        late_release.set()
        spin(late_done.is_set)
        for _ in range(20):
            app.processEvents(QEventLoop.AllEvents, 20)
            time.sleep(.005)
        assert not callbacks and flow.access_token() is None
        assert not transport.in_flight
        results['cancel_late_native_reply'] = True
        transport.close()
        mode[0] = 'oversize'
        transport = LoopbackTransport()
        callbacks = []
        assert transport.send(Request((8, 1), 'device', {'client_id': 'x', 'scope': 'offline_access'}),
                              lambda key, status, body: callbacks.append((status, body)))
        spin(lambda: bool(callbacks))
        assert callbacks == [(0, {})], 'oversized native response was not refused'
        results['oversized_response_refused'] = True
        transport.close()
        mode[0] = 'duplicate'
        transport = LoopbackTransport()
        callbacks = []
        assert transport.send(Request((8, 2), 'device', {'client_id': 'x', 'scope': 'offline_access'}),
                              lambda key, status, body: callbacks.append((status, body)))
        spin(lambda: bool(callbacks))
        assert callbacks == [(0, {})], 'duplicate JSON response was not refused'
        results['duplicate_response_refused'] = True
        transport.close()
        mode[0] = 'mixed'
        transport = LoopbackTransport()
        callbacks = []
        assert transport.send(Request((8, 3), 'device', {'client_id': 'x', 'scope': 'offline_access'}),
                              lambda key, status, body: callbacks.append((status, body)))
        spin(lambda: bool(callbacks))
        assert callbacks == [(0, {})], 'mixed error/refresh response was not refused before filtering'
        results['mixed_response_refused'] = True
        transport.close()
        mode[0] = 'parent'
        late_started.clear(); late_release.clear(); late_done.clear()
        parent = QObject()
        transport = LoopbackTransport(parent)
        callbacks = []
        assert transport.send(Request((8, 4), 'device', {'client_id': 'x', 'scope': 'offline_access'}),
                              lambda *args: callbacks.append(True))
        spin(late_started.is_set)
        parent.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        late_release.set()
        spin(late_done.is_set)
        for _ in range(20):
            app.processEvents(QEventLoop.AllEvents, 20); time.sleep(.005)
        assert not callbacks and transport._reply is None, 'parent teardown left native request active'
        transport = None
        results['parent_teardown_aborts'] = True
        transport = LoopbackTransport()
        for bad in (Request((8, 5), 'refresh', {'client_id': 'x'}),
                    Request((8, 5), 'device', {'client_id': 'x', 'scope': 'repo'}),
                    Request((8, 5), 'device', {'client_id': 'x', 'scope': 'offline_access', 'extra': 'x'})):
            assert not transport.send(bad, lambda *args: None)
        results['invalid_requests_not_sent'] = True
        mode[0] = 'redirect'
        print('boundary: redirect', flush=True)
        callbacks = []
        assert transport.send(Request((8, 6), 'device', {'client_id': 'x', 'scope': 'offline_access'}),
                              lambda key, status, body: callbacks.append((status, body)))
        spin(lambda: bool(callbacks))
        assert callbacks == [(0, {})] and not any(path == '/sink' for _, path, _ in posted)
        results['redirect_not_followed'] = True
        transport.close()
        mode[0] = 'timeout'
        print('boundary: timeout', flush=True)
        late_started.clear(); late_release.clear(); late_done.clear()
        class FastTransport(LoopbackTransport):
            REQUEST_TIMEOUT_MS = 100
        transport = FastTransport()
        callbacks = []
        assert transport.send(Request((8, 7), 'device', {'client_id': 'x', 'scope': 'offline_access'}),
                              lambda key, status, body: callbacks.append((status, body)))
        spin(late_started.is_set)
        spin(lambda: bool(callbacks))
        assert callbacks == [(0, {})] and not transport.in_flight
        late_release.set(); spin(late_done.is_set)
        results['native_timeout_aborts'] = True
        transport.close()
        mode[0] = 'tls'
        class UntrustedTlsTransport(module.GitHubDeviceTransport):
            def _endpoint_url(self, endpoint):
                return 'https://127.0.0.1:' + str(tls_server.server_port) + '/' + endpoint
        transport = UntrustedTlsTransport()
        callbacks, tls_errors = [], []
        before_posts, before_seen = len(posted), len(seen)
        assert transport.send(Request((8, 9), 'token', {'client_id': 'synthetic-client',
                              'device_code': device_marker,
                              'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'}),
                              lambda key, status, body: callbacks.append((status, body)))
        transport._reply.sslErrors.connect(lambda errors: tls_errors.append(bool(errors)))
        spin(lambda: bool(callbacks))
        assert callbacks == [(0, {})] and not transport.in_flight
        assert tls_errors and all(tls_errors), 'actual adapter did not encounter untrusted TLS'
        assert len(posted) == before_posts, 'untrusted TLS delivered an HTTP POST'
        assert len(seen) == before_seen + 1
        assert device_marker.encode() in seen[-1][2], 'TLS request observer did not expose code'
        results['exact_adapter_untrusted_tls_refused'] = True
        results['tls_http_posts'] = len(posted) - before_posts
        results['observer_device_code_visible'] = any(device_marker.encode() in body for _, _, body in seen)
        assert results['observer_device_code_visible'], 'observer exposure was not actually exercised'
        transport.close()
        mode[0] = 'quit'
        late_started.clear(); late_release.clear(); late_done.clear()
        transport = LoopbackTransport()
        callbacks = []
        assert transport.send(Request((8, 8), 'device', {'client_id': 'x', 'scope': 'offline_access'}),
                              lambda *args: callbacks.append(True))
        quit_poll = QTimer()
        quit_poll.timeout.connect(lambda: app.quit() if late_started.is_set() else None)
        quit_poll.start(5)
        guard = QTimer()
        guard.setSingleShot(True); guard.timeout.connect(app.quit); guard.start(3000)
        print('boundary: before native quit loop', flush=True)
        app.exec()
        print('boundary: after native quit loop', flush=True)
        guard.stop(); quit_poll.stop()
        assert late_started.is_set() and not transport.in_flight and transport._closed
        late_release.set(); spin(late_done.is_set)
        assert not callbacks
        results['actual_about_to_quit_aborts'] = True
        assert len(posted) == 10 and len(seen) == 11
        assert all(host == '127.0.0.1' and not auth for host, auth, _ in seen)
        assert not logged and manager.timeout() == original_timeout
        results.update(product_action_wired=False, provider_contacted=False, native_requests=len(seen),
                       native_http_posts=len(posted),
                       observer_body_visible=all(bool(body) for _, _, body in seen),
                       observed_message_log_marker_absent=True,
                       module_origin=str(plugin / 'github_transport.py'))
        (root / 'assertions.json').write_text(json.dumps(results, indent=2))
        print('Packaged native model/transport success and real cancel/late-reply checks passed.')
    finally:
        late_release.set()
        if transport:
            transport.close()
        signal.disconnect(observe)
        QgsApplication.messageLog().messageReceived.disconnect(log)
        tls_server.shutdown()
        tls_server.server_close()
        tls_thread.join(timeout=3)
        assert not tls_thread.is_alive()
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        app.exitQgis()


if __name__ == '__main__':
    main()
