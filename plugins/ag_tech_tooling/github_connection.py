# SPDX-License-Identifier: GPL-2.0-or-later
"""Optional GitHub connection UI. Production sends are deliberately disabled.

No registered client or diagnostic-safe real-send boundary is supplied. Local
work stays offline. Native widgets are lifecycle-owned, not an authentication claim.
"""
import time

from .github_session import SessionDeviceFlow
from qgis.PyQt.QtCore import QObject, QCoreApplication, QTimer, Qt
from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class ConnectionDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Ag-GIS — GitHub Connection')
        self.setMinimumWidth(450)
        layout = QVBoxLayout(self)
        self.notice = QLabel('Ag-GIS and agent instructions work offline without sign-in. '\
                             'No farm records or reports are sent by this window.', self)
        self.notice.setWordWrap(True)
        self.notice.setToolTip('Offline mode notice: Ag-GIS works without GitHub sign-in')
        layout.addWidget(self.notice)
        self.status = QLabel('GitHub sign-in is unavailable: app registration and '\
                             'diagnostic-safe connection checks are not complete.', self)
        self.status.setWordWrap(True)
        self.status.setToolTip('GitHub connection status: sign-in unavailable')
        layout.addWidget(self.status)
        self.user_code = QLabel('', self)
        self.user_code.setTextFormat(Qt.PlainText)
        self.user_code.setToolTip('Authentication code displayed here')
        layout.addWidget(self.user_code)
        row = QHBoxLayout()
        self.connect_button = QPushButton('Connect', self)
        self.connect_button.setEnabled(False)
        self.connect_button.setToolTip('Connect to GitHub is disabled: sign-in is unavailable and Ag-GIS works offline.')
        self.connect_button.setProperty('aria-label', 'Connect to GitHub is disabled')
        self.cancel_button = QPushButton('Cancel connection', self)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setToolTip('Cancel connection is disabled: no active connection to cancel.')
        self.cancel_button.setProperty('aria-label', 'Cancel connection is disabled')
        self.close_button = QPushButton('Close', self)
        self.close_button.clicked.connect(self.reject)
        self.close_button.setToolTip('Close the connection dialog and return to Ag-GIS.')
        self.close_button.setProperty('aria-label', 'Close the connection dialog')
        for button in (self.connect_button, self.cancel_button, self.close_button):
            row.addWidget(button)
        layout.addLayout(row)


class GitHubConnection(QObject):
    """One owned session/dialog. Default product path has no network factory.

    _fixture_factory is private dependency injection for synthetic native tests,
    NOT a settings/client/host override or a supported real-credential path.
    """
    def __init__(self, parent, *, _fixture_factory=None):
        super().__init__(parent)
        self.dialog = None
        self.flow = None
        self.closed = False
        self._fixture_factory = _fixture_factory
        self._transport = None
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._advance)
        self._app = QCoreApplication.instance()
        if self._app is not None:
            self._app.aboutToQuit.connect(self.close)
        parent.destroyed.connect(self.close)

    def open(self):
        if self.closed:
            return
        if self.dialog is None:
            self.dialog = ConnectionDialog(self.parent())
            self.dialog.connect_button.clicked.connect(self.start)
            self.dialog.cancel_button.clicked.connect(self.cancel)
            self.dialog.finished.connect(self.cancel)
        self._sync()
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def start(self):
        # UI disabling alone is not a real-send gate. No factory is provided by
        # production startup, settings, environment, client IDs or user input.
        if (self.closed or self._fixture_factory is None or self.dialog is None
                or (self.flow is not None and self.flow.state in ('requesting', 'waiting', 'authorized'))):
            return False
        self.cancel()
        self.flow = SessionDeviceFlow(time.monotonic)
        try:
            client, self._transport = self._fixture_factory(self)
            request = self.flow.start(client)
            self._send(request)
        except Exception:
            # Deliberate fixed error state: never persist/display exception text.
            self.flow._stop('failed')
        self._sync()
        if self.flow.state in ('requesting', 'waiting', 'authorized'):
            self.timer.start()
        return self.flow.state != 'failed'

    def _send(self, request):
        if request is None:
            return
        flow = self.flow
        callback = lambda key, status, body: self._receive(flow, key, status, body)
        if self._transport is None or not self._transport.send(request, callback):
            flow.receive(request.key, 0, {})

    def _receive(self, flow, key, status, body):
        # Each fresh flow starts numbering at zero. Its object identity is also
        # required, or an old callback could collide with a new flow's tuple key.
        if self.closed or flow is not self.flow:
            return
        flow.receive(key, status, body)
        self._sync()

    def _advance(self):
        if self.closed or self.flow is None:
            return
        self.flow.tick()
        self._send(self.flow.poll())
        self._sync()

    def _sync(self):
        if self.dialog is None:
            return
        dialog = self.dialog
        state = self.flow.state if self.flow is not None else 'idle'
        active = state in ('requesting', 'waiting', 'authorized')
        dialog.connect_button.setEnabled(self._fixture_factory is not None and not active and not self.closed)
        dialog.cancel_button.setEnabled(active and not self.closed)
        dialog.user_code.setText(self.flow.user_code or '' if self.flow is not None else '')
        if self._fixture_factory is not None:
            messages = {'idle': 'Synthetic connection test only. No real GitHub sign-in.',
                        'requesting': 'Requesting a synthetic connection code…',
                        'waiting': 'Synthetic code ready. Waiting for the test server.',
                        'authorized': 'Synthetic session connected for this process only.',
                        'cancelled': 'Connection cancelled. Local work remains available.',
                        'expired': 'Session expired. Start a fresh connection.',
                        'failed': 'Connection failed. Local work remains available.',
                        'denied': 'Connection declined. Local work remains available.',
                        'unconfigured': 'Connection is not configured. Local work remains available.'}
            dialog.status.setText(messages[state])
        if not active:
            self.timer.stop()
            if self._transport is not None:
                self._transport.close()
                self._transport = None

    def cancel(self, *_):
        self.timer.stop()
        if self.flow is not None:
            self.flow.cancel()
        if self._transport is not None:
            self._transport.close()
            self._transport = None
        self._sync()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.cancel()
        if self._app is not None:
            self._app.aboutToQuit.disconnect(self.close)
            self._app = None
        dialog, self.dialog = self.dialog, None
        if dialog is not None:
            dialog.finished.disconnect(self.cancel)
            dialog.reject()
            dialog.deleteLater()
