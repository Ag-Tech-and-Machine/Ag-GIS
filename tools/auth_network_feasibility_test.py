# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

    """Synthetic-only native QGIS network boundary experiment, NOT a login adapter.

    

    Use run_auth_network_feasibility.py. HTTP is confined to ephemeral loopback test

    servers; real authentication requires HTTPS and an independently reviewed adapter.

    No credentials, auth-method expansion, product imports or provider requests.

    """

    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from pathlib import Path

    import gc

    import json

    import os

    import ssl

    import threading

    import time

    

    

    def main():

        root = Path(os.environ['AGGIS_SYNTHETIC_NETWORK_ROOT']).resolve()

        base = Path('C:/Users/Michael/AppData/Local/hermes/cache/scratch').resolve()

        assert root.is_relative_to(base) and root.name.startswith('aggis-auth-network-')

        assert (root / 'SYNTHETIC-ONLY').read_text() == 'native-loopback-v1'

        marker = os.environ['AGGIS_SYNTHETIC_NETWORK_MARKER'].encode('ascii')

        assert marker.startswith(b'AGGIS-SYNTHETIC-NETWORK-')

        os.environ['QT_QPA_PLATFORM'] = 'offscreen'

        os.environ['QGIS_AUTH_DB_DIR_PATH'] = str(root / 'auth')

        (root / 'auth').mkdir()

        from qgis.PyQt.QtCore import QSettings, QTimer, QUrl, QCoreApplication, QEvent

        from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
    try:
        from qgis.core import (QgsApplication, QgsNetworkAccessManager,
                       QgsNetworkRequestParameters, Qgis)
    except ImportError:
        pass  # QGIS not available, skip this import
    QSettings.setDefaultFormat(QSettings.IniFormat)

    for scope in (QSettings.UserScope, QSettings.SystemScope):

        QSettings.setPath(QSettings.IniFormat, scope, str(root / 'settings'))

    app = QgsApplication([], False, str(root / 'profile'))

    app.initQgis()

    manager = QgsNetworkAccessManager.instance()

    global_timeout = manager.timeout()

    requests = []

    observer = []

    log_leak = []

    unexpected = []

    delayed_started = threading.Event()

    delayed_release = threading.Event()

    delayed_finished = threading.Event()

    servers = []

    threads = []

    results = {}

    live_replies = []

    state = {}



    class Handler(BaseHTTPRequestHandler):

        protocol_version = 'HTTP/1.1'



        def log_message(self, *args):

            # Test server has no request logger; native logging is not modified.

            pass



        def do_POST(self):

            data = self.rfile.read(int(self.headers.get('Content-Length', '0')))

            requests.append({'path': self.path,

                             'header_exact': self.headers.get('Authorization', '').encode() == b'Bearer ' + marker,

                             'body_exact': data == b'device_code=' + marker,

                             'port': self.server.server_port})

            if self.path in ('/cancel', '/timeout'):

                delayed_started.set()

                delayed_release.wait(5)

            status = 307 if self.path == '/redirect' else 200

            body = b'{"access_token":"' + marker + b'"}'

            try:

                self.send_response(status)

                if status == 307:

                    self.send_header('Location', 'http://localhost:' + str(sink.server_port) + '/sink')

                self.send_header('Content-Length', str(len(body)))

                self.send_header('Connection', 'close')

                self.end_headers()

                self.wfile.write(body)

            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):

                pass  # Expected only after test-owned native abort.

            finally:

                if self.path in ('/cancel', '/timeout'):

                    delayed_finished.set()



    def server(tls=False):

        item = ThreadingHTTPServer(('127.0.0.1', 0), Handler)

        item.daemon_threads = True

        if tls:

            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

            context.load_cert_chain(str(root / 'cert.pem'), str(root / 'key.pem'))

            item.socket = context.wrap_socket(item.socket, server_side=True)

        worker = threading.Thread(target=item.serve_forever, daemon=True)

        worker.start()

        servers.append(item)

        threads.append(worker)

        return item



    def observe(params):

        req = params.request()

        # Intentionally demonstrate observer exposure, never persist the bytes.

        observer.append({'header_visible': bytes(req.rawHeader(b'Authorization')) == b'Bearer ' + marker,

                         'body_visible': bytes(params.content()) == b'device_code=' + marker,

                         'loopback': req.url().host() == '127.0.0.1'})



    def logged(message, tag, level):

        if marker.decode() in message or marker.decode() in tag:

            log_leak.append(True)



    signal = manager.requestAboutToBeCreated[QgsNetworkRequestParameters]

    signal.connect(observe)

    QgsApplication.messageLog().messageReceived.connect(logged)

    watchdog = QTimer()

    watchdog.setSingleShot(True)

    watchdog.timeout.connect(lambda: (unexpected.append('watchdog'), app.quit()))

    watchdog.start(15000)

    tick = QTimer()

    tick.setInterval(10)

    deadline_timer = QTimer()

    deadline_timer.setSingleShot(True)



    def fail_closed(label):

        # Test-local state, not product cancellation or DeviceFlow integration.

        state['terminal'] = label

        if state.get('reply') and not state['reply'].isFinished():

            state['reply'].abort()

        delayed_release.set()



    def tick_cancel():

        if state.get('kind') == 'cancel' and delayed_started.is_set():

            fail_closed('cancelled')



    tick.timeout.connect(tick_cancel)

    tick.start()

    deadline_timer.timeout.connect(lambda: fail_closed('timed_out'))



    def start(kind):

        delayed_started.clear()

        delayed_release.clear()

        delayed_finished.clear()

        state.clear()

        state.update(kind=kind, terminal=None, callbacks=0, accepted=0, ssl_errors=0,

                     started=time.monotonic())

        target = secure if kind == 'tls' else origin

        scheme = 'https' if kind == 'tls' else 'http'

        req = QNetworkRequest(QUrl(scheme + '://127.0.0.1:' + str(target.server_port) + '/' + kind))

        req.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.ManualRedirectPolicy)

        req.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)

        req.setAttribute(QNetworkRequest.CacheSaveControlAttribute, False)

        req.setAttribute(QNetworkRequest.CookieLoadControlAttribute, QNetworkRequest.Manual)

        req.setAttribute(QNetworkRequest.CookieSaveControlAttribute, QNetworkRequest.Manual)

        req.setHeader(QNetworkRequest.ContentTypeHeader, 'application/x-www-form-urlencoded')

        req.setRawHeader(b'Authorization', b'Bearer ' + marker)

        reply = manager.post(req, b'device_code=' + marker)

        live_replies.append(reply)

        state['reply'] = reply

        reply.sslErrors.connect(lambda errors: state.update(ssl_errors=state['ssl_errors'] + len(errors)))

        reply.finished.connect(lambda: finished(kind, reply))

        if kind == 'timeout':

            deadline_timer.start(180)



    def finished(kind, reply):

        deadline_timer.stop()

        state['callbacks'] += 1

        error = reply.error()

        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        body = b'' if error else bytes(reply.readAll())

        if state['terminal'] is None and error == QNetworkReply.NoError and status == 200:

            state['accepted'] += int(body == b'{"access_token":"' + marker + b'"}')

        results[kind] = {'error': int(error), 'status': status, 'callbacks': state['callbacks'],

                         'accepted': state['accepted'], 'terminal': state['terminal'],

                         'ssl_errors': state['ssl_errors'], 'elapsed': time.monotonic() - state['started']}

        # Give the real server a turn to attempt its late response, then assert no

        # callback revival. No fabricated response/callback is injected.

        delayed_release.set()

        QTimer.singleShot(400, lambda: checked(kind, reply))



    def checked(kind, reply):

        try:

            result = results[kind]

            assert state['callbacks'] == 1 and result['callbacks'] == 1

            if kind == 'success':

                assert result['accepted'] == 1 and result['status'] == 200 and result['error'] == 0

                assert len(requests) == 1 and requests[0]['header_exact'] and requests[0]['body_exact']

                results['observer_exposure'] = {'header_visible': observer[0]['header_visible'],

                                                'body_visible': observer[0]['body_visible']}

                assert all(results['observer_exposure'].values())

            elif kind in ('cancel', 'timeout'):

                assert delayed_started.is_set() and delayed_finished.is_set()

                assert result['terminal'] == ('cancelled' if kind == 'cancel' else 'timed_out')

                assert result['accepted'] == 0 and result['error'] == int(QNetworkReply.OperationCanceledError)

                assert result['elapsed'] < 3

            elif kind == 'redirect':

                assert result['status'] == 307 and result['accepted'] == 0 and result['error'] == 0

                assert not any(item['port'] == sink.server_port for item in requests)

                assert reply.attribute(QNetworkRequest.RedirectionTargetAttribute).path() == '/sink'

            elif kind == 'tls':

                assert result['error'] == int(QNetworkReply.SslHandshakeFailedError)

                assert result['accepted'] == 0 and result['ssl_errors'] > 0

                assert not any(item['port'] == secure.server_port for item in requests)

            reply.deleteLater()

            live_replies.remove(reply)

            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

            order = ['success', 'cancel', 'timeout', 'redirect', 'tls']

            index = order.index(kind) + 1

            if index == len(order):

                app.quit()

            else:

                QTimer.singleShot(0, lambda: start(order[index]))

        except Exception as exc:

            unexpected.append(type(exc).__name__ + ':' + kind)

            app.quit()



    try:

        origin, sink, secure = server(), server(), server(tls=True)

        QTimer.singleShot(0, lambda: start('success'))

        app.exec()

        assert not unexpected, 'Native feasibility assertions failed: ' + repr(unexpected)

        assert set(results) == {'success', 'cancel', 'timeout', 'redirect', 'tls', 'observer_exposure'}

        assert len(requests) == 4 and len(observer) == 5 and all(x['loopback'] for x in observer)

        assert all(x['header_exact'] and x['body_exact'] for x in requests)

        assert not log_leak, 'Synthetic marker present in observed native message log'

        assert manager.timeout() == global_timeout

        results['boundaries'] = {'http_requests': len(requests), 'native_observations': len(observer),

                                 'native_message_log_marker_absent': True, 'global_timeout_unchanged': True,

                                 'synthetic_only': True, 'product_wired': False, 'qgis': Qgis.QGIS_VERSION}

        (root / 'assertions.json').write_text(json.dumps(results, indent=2), encoding='utf-8')

        print('Five native synthetic loopback cases asserted; observer exposure confirmed.')

    finally:

        watchdog.stop()

        tick.stop()

        deadline_timer.stop()

        delayed_release.set()

        signal.disconnect(observe)

        QgsApplication.messageLog().messageReceived.disconnect(logged)

        for reply in live_replies:

            reply.abort()

            reply.deleteLater()

        live_replies.clear()

        for item in servers:

            item.shutdown()

            item.server_close()

        for worker in threads:

            worker.join(timeout=3)

            assert not worker.is_alive()

        state.clear()

        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        gc.collect()

        app.exitQgis()





except Exception as exc:
    print(f"Module-level error: {{exc}}")
    sys.exit(1)
if __name__ == '__main__':

    main()


