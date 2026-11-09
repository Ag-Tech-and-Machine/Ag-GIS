# SPDX-License-Identifier: GPL-2.0-or-later
"""Inactive native device-flow transport; not a configured product login.

No browser, settings, storage, refresh, identity lookup or issue submission. No
caller-configurable URL or client registration. Future session controller must
cancel on close/unload and enforce model generation/expiry before accepting.
QGIS request observers can see POST bodies; this is NOT a secret process boundary.
Do not pass real credentials before logging/observer and registration gates clear.
"""
import json
from urllib.parse import urlencode

from qgis.PyQt.QtCore import QObject, QCoreApplication, QTimer, QUrl
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest
from qgis.core import QgsNetworkAccessManager


class GitHubDeviceTransport(QObject):
    """One cancellable native request. Instantiation never sends a request.

    send accepts a device-model Request and callback(key, status, allowlisted body).
    cancel is silent; terminal transport failures call back once with 0/{}. No
    automatic retries, redirects, auth configuration expansion or raw diagnostics.
    close permanently disables the instance and detaches its quit connection.
    """
    MAX_RESPONSE_BYTES = 65536
    REQUEST_TIMEOUT_MS = 30000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._reply = None
        self._callback = self._key = None
        self._closed = False
        self._buffer = bytearray()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._timeout)
        self._app = QCoreApplication.instance()
        if self._app is not None:
            self._app.aboutToQuit.connect(self.close)
        if parent is not None:
            parent.destroyed.connect(self.close)

    @property
    def in_flight(self):
        return self._reply is not None

    def _endpoint_url(self, endpoint):
        return {'device': 'https://github.com/login/device/code',
                'token': 'https://github.com/login/oauth/access_token'}[endpoint]

    @staticmethod
    def _valid(request):
        endpoint = getattr(request, 'endpoint', None)
        payload = getattr(request, 'payload', None)
        if type(payload) is not dict:
            return False
        expected = {'device': {'client_id', 'scope'},
                    'token': {'client_id', 'device_code', 'grant_type'}}
        if endpoint not in expected or set(payload) != expected[endpoint]:
            return False
        if any(type(v) is not str or not 0 < len(v) <= 8192
               or not all(32 < ord(c) < 127 for c in v) for v in payload.values()):
            return False
        if len(payload['client_id']) > 256:
            return False
        if endpoint == 'device':
            return payload['scope'] == 'offline_access'
        return (len(payload['device_code']) == 40
                and payload['grant_type'] == 'urn:ietf:params:oauth:grant-type:device_code')

    def send(self, request, callback):
        if self._closed or self.in_flight or not callable(callback) or not self._valid(request):
            return False
        req = QNetworkRequest(QUrl(self._endpoint_url(request.endpoint)))
        req.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.ManualRedirectPolicy)
        req.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
        req.setAttribute(QNetworkRequest.CacheSaveControlAttribute, False)
        req.setAttribute(QNetworkRequest.CookieLoadControlAttribute, QNetworkRequest.Manual)
        req.setAttribute(QNetworkRequest.CookieSaveControlAttribute, QNetworkRequest.Manual)
        req.setHeader(QNetworkRequest.ContentTypeHeader, 'application/x-www-form-urlencoded')
        req.setRawHeader(b'Accept', b'application/json')
        self._callback, self._key = callback, request.key
        self._buffer.clear()
        self._reply = QgsNetworkAccessManager.instance().post(req, urlencode(dict(request.payload)).encode('ascii'))
        self._reply.setReadBufferSize(self.MAX_RESPONSE_BYTES + 1)
        self._reply.readyRead.connect(self._read)
        self._reply.finished.connect(self._finished)
        self._timer.start(self.REQUEST_TIMEOUT_MS)
        return True

    def _read(self):
        if self._reply is not None and self._reply.bytesAvailable() > 0:
            remaining = self.MAX_RESPONSE_BYTES + 1 - len(self._buffer)
            self._buffer.extend(bytes(self._reply.read(remaining)))
            if len(self._buffer) > self.MAX_RESPONSE_BYTES:
                self._timeout()

    @staticmethod
    def _body(raw):
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError('Duplicate response key')
                result[key] = value
            return result
        body = json.loads(raw, object_pairs_hook=unique)
        if type(body) is not dict:
            return {}
        if 'error' in body and ('access_token' in body or 'refresh_token' in body):
            raise ValueError('Mixed response')
        # Drop refresh credentials and arbitrary provider prose at this boundary.
        allowed = {'device_code', 'user_code', 'verification_uri', 'interval', 'expires_in',
                   'access_token', 'token_type', 'error'}
        return {k: v for k, v in body.items() if k in allowed}

    def _finished(self):
        reply = self._reply
        if reply is None:
            return
        self._read()
        if self._reply is not reply:
            return
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        body = {}
        if reply.error() == QNetworkReply.NoError and type(status) is int and status == 200:
            try:
                body = self._body(bytes(self._buffer))
            except (ValueError, UnicodeError, RecursionError):
                status = 0
        else:
            status = 0
        callback, key = self._callback, self._key
        self.cancel()
        if callback is not None:
            callback(key, status, body)

    def _timeout(self):
        callback, key = self._callback, self._key
        self.cancel()
        if callback is not None:
            callback(key, 0, {})

    def cancel(self):
        self._timer.stop()
        reply, self._reply = self._reply, None
        self._callback = self._key = None
        self._buffer.clear()
        if reply is not None:
            reply.readyRead.disconnect(self._read)
            reply.finished.disconnect(self._finished)
            if not reply.isFinished():
                reply.abort()
            reply.deleteLater()

    def close(self):
        if self._closed:
            return
        self._closed = True
        self.cancel()
        if self._app is not None:
            self._app.aboutToQuit.disconnect(self.close)
            self._app = None
