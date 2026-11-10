"""QGIS application recorder/export audit, synthetic loopback only.

Executed by run_github_recorder_test.py using the real QGIS desktop binary.
This demonstrates a known diagnostic exposure; passing is NOT security clearance.
Never reads or writes the system clipboard. Qt file-dialog automation is not
Windows native-picker or branded Ag-GIS acceptance.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from qgis.core import QgsApplication, QgsNetworkAccessManager, QgsSettings, Qgis
from qgis.PyQt.QtCore import QTimer, QEventLoop, Qt, QObject
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtWidgets import QApplication, QAction, QTreeView, QMessageBox, QFileDialog
from qgis.utils import iface

ROOT = Path(os.environ['AGGIS_RECORDER_SCRATCH']).resolve()
PLUGIN = Path(os.environ['AGGIS_RECORDER_PLUGIN']).resolve()
RESULT = {'passed': False, 'real_credentials_cleared': False, 'clipboard_touched': False,
          'curl_action_executed': False, 'branded_acceptance': False}
KEEP = []
DEVICE = 'SYNTHETIC-RECORDER-' + 'd' * 21
HEADER = 'SYNTHETIC-RECORDER-HEADER'


def spin(predicate, seconds=6):
    until = time.monotonic() + seconds
    while not predicate() and time.monotonic() < until:
        QApplication.processEvents(QEventLoop.AllEvents, 20)
        time.sleep(.005)
    assert predicate(), 'native recorder event deadline'


def module(name):
    spec = importlib.util.spec_from_file_location('recorder_' + name, PLUGIN / (name + '.py'))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    assert Path(mod.__file__).resolve() == PLUGIN / (name + '.py')
    return mod


def run():
    server = None
    transport = None
    try:
        assert ROOT.is_relative_to(Path('C:/Users/[Maintainer]/AppData/Local/hermes/cache/scratch').resolve())
        assert ROOT.name.startswith('aggis-recorder-')
        assert (ROOT / 'SYNTHETIC-ONLY').read_text() == 'recorder-v1'
        profile = Path(QgsApplication.qgisSettingsDirPath()).resolve()
        settings = Path(QgsSettings().fileName()).resolve()
        auth = Path(QgsApplication.qgisAuthDatabaseFilePath()).resolve()
        assert all(p.is_relative_to(ROOT) for p in (profile, settings, auth)), 'native profile isolation'
        assert not iface.mainWindow().isWindowModified()
        RESULT.update(pid=os.getpid(), qgis_version=Qgis.QGIS_VERSION, profile=str(profile),
                      settings=str(settings), auth_path=str(auth), platform=QApplication.platformName())
        assert len(DEVICE) == 40
        w = iface.mainWindow()
        panels = [o for o in w.findChildren(QObject)
                  if o.metaObject().className() == 'QgsNetworkLoggerPanelWidget']
        assert len(panels) == 1
        panel = panels[0]
        tree = next(o for o in panel.findChildren(QTreeView)
                    if o.metaObject().className() == 'QgsNetworkLoggerTreeView')
        model = tree.model()
        assert model.sourceModel().metaObject().className() == 'QgsNetworkLogger'
        record = panel.findChild(QAction, 'mActionRecord')
        save = panel.findChild(QAction, 'mActionSaveLog')
        clear = panel.findChild(QAction, 'mActionClear')
        assert record and save and clear and not record.isChecked()
        assert model.rowCount() == 0
        posted = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                posted.append((self.path, body, self.headers.get('Authorization', '')))
                data = json.dumps({'error': 'authorization_pending'}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        manager = QgsNetworkAccessManager.instance()
        transport_module = module('github_transport')
        producer = module('github_session')

        class LoopbackTransport(transport_module.GitHubDeviceTransport):
            def _endpoint_url(self, endpoint):
                return 'http://127.0.0.1:' + str(server.server_port) + '/' + endpoint

        transport = LoopbackTransport(w)
        # Construct the token poll through the actual packaged producer; no provider.
        clock = [100.0]
        flow = producer.SessionDeviceFlow(lambda: clock[0])
        initial = flow.start('SYNTHETIC-RECORDER-CLIENT')
        assert flow.receive(initial.key, 200, dict(device_code=DEVICE, user_code='ABCD-EFGH',
                           verification_uri='https://github.com/login/device', interval=1, expires_in=60))
        clock[0] += 1
        request = flow.poll()
        assert request is not None and request.endpoint == 'token'

        def poll_once():
            callbacks = []
            assert transport.send(request, lambda *args: callbacks.append(args))
            spin(lambda: bool(callbacks))
            assert len(callbacks) == 1 and callbacks[0][1:] == (200, {'error': 'authorization_pending'})
            return callbacks[0]

        poll_once()
        assert len(posted) == 1 and model.rowCount() == 0
        RESULT['recording_off_does_not_add_rows'] = True
        record.trigger()
        assert record.isChecked()
        reply = poll_once()
        assert flow.receive(*reply) and flow.state == 'waiting'
        spin(lambda: model.rowCount() == 1)

        def values(parent=None):
            from qgis.PyQt.QtCore import QModelIndex
            parent = parent if parent is not None else QModelIndex()
            result = []
            for row in range(model.rowCount(parent)):
                index = model.index(row, 0, parent)
                result.append(str(model.data(index, Qt.DisplayRole)))
                result += values(index)
            return result

        assert DEVICE in '\n'.join(values()), 'native recorder did not retain device-code POST body'
        RESULT['packaged_poll_body_retained'] = True
        # Independent native header fixture, NOT a header sent by product transport.
        from qgis.PyQt.QtCore import QUrl
        req = QNetworkRequest(QUrl('http://127.0.0.1:' + str(server.server_port) + '/header-fixture'))
        req.setRawHeader(b'Authorization', ('Bearer ' + HEADER).encode())
        native = manager.post(req, b'synthetic=header-fixture')
        spin(native.isFinished)
        assert native.error() == native.NoError
        native.deleteLater()
        spin(lambda: model.rowCount() == 2)
        assert HEADER in '\n'.join(values())
        RESULT['independent_native_header_retained'] = True
        record.trigger()
        assert not record.isChecked()
        poll_once()
        assert len(posted) == 4 and model.rowCount() == 2
        assert DEVICE in '\n'.join(values()) and HEADER in '\n'.join(values())
        RESULT['disable_preserves_old_rows_but_stops_new_rows'] = True

        # Activate native context-menu construction but never a clipboard action.
        # The rows may be in a hidden developer panel; expose only this scratch app.
        panel.show()
        tree.expandAll()
        tree.resize(900, 500)
        tree.show()
        QApplication.processEvents()
        index = model.index(0, 0)
        tree.scrollTo(index)
        menus = []
        from qgis.PyQt.QtWidgets import QMenu
        def dismiss_menu():
            for menu in tree.findChildren(QMenu):
                if menu.isVisible():
                    menus.extend(a.text() for a in menu.actions())
                    menu.close()
        QTimer.singleShot(100, dismiss_menu)
        tree.customContextMenuRequested.emit(tree.visualRect(index).center())
        assert 'Copy As cURL' in menus and 'Copy as JSON' in menus
        RESULT['native_curl_action_present_not_triggered'] = True

        # Actual native Save Log C++ lambda, with real warning + Qt file picker.
        # This attribute applies only in this synthetic process, never owner settings.
        QApplication.setAttribute(Qt.AA_DontUseNativeDialogs, True)
        interactions = []
        target = ROOT / 'synthetic-network-log.json'
        mode = ['no']
        timer = QTimer(w)
        timer.setInterval(40)
        KEEP.append(timer)
        def respond():
            modal = QApplication.activeModalWidget()
            (ROOT / 'interaction-progress.json').write_text(json.dumps(dict(mode=mode[0], interactions=interactions[-12:], modal=modal.metaObject().className() if modal else None, python_type=type(modal).__name__)))
            if isinstance(modal, QMessageBox) and modal.windowTitle() == 'Save Network Log':
                assert 'sensitive data' in modal.text() and 'confidential' in modal.text()
                interactions.append(mode[0] + '-warning')
                # Return from timeout first: clicking Yes synchronously opens a
                # nested picker while this timer cannot re-enter its own slot.
                QTimer.singleShot(0, modal.button(QMessageBox.No if mode[0] == 'no' else QMessageBox.Yes).click)
            elif isinstance(modal, QFileDialog):
                if not interactions or interactions[-1] != mode[0] + '-picker':
                    interactions.append(mode[0] + '-picker')
                if mode[0] == 'cancel':
                    modal.reject()
                else:
                    if not modal.property('fixture_ready'):
                        modal.setDirectory(str(ROOT))
                        modal.setProperty('fixture_ready', True)
                        return
                    from qgis.PyQt.QtWidgets import QLineEdit
                    filename = modal.findChild(QLineEdit, 'fileNameEdit')
                    assert filename is not None
                    filename.setText(target.name)
                    QTimer.singleShot(0, modal.accept)
        timer.timeout.connect(respond)
        timer.start()
        save.trigger()
        assert interactions == ['no-warning'] and not target.exists()
        mode[0] = 'cancel'
        save.trigger()
        assert interactions[-2:] == ['cancel-warning', 'cancel-picker'] and not target.exists()
        mode[0] = 'export'
        save.trigger()
        timer.stop()
        assert interactions[-2:] == ['export-warning', 'export-picker'] and target.is_file()
        exported = json.loads(target.read_text())
        assert type(exported) is list and len(exported) == 2
        text = json.dumps(exported)
        assert DEVICE in text and HEADER in text
        assert all('127.0.0.1' in row['URL'] for row in exported)
        RESULT.update(export_warning_no_no_write=True, export_picker_cancel_no_write=True,
                      explicit_native_export_contains_retained_body_and_header=True,
                      exported_rows=len(exported), server_posts=len(posted), interactions=interactions)
        # Do not retain synthetic payload dumps as habitual diagnostics artifacts.
        target.unlink()
        assert not target.exists()
        clear.trigger()
        assert model.rowCount() == 0
        RESULT['explicit_scratch_clear_removes_rows'] = True
        transport.close()
        assert not transport.in_flight
        RESULT['passed'] = True
    except Exception:
        RESULT['error'] = traceback.format_exc()
    finally:
        if transport is not None:
            transport.close()
        if server is not None:
            server.shutdown()
            server.server_close()
        (ROOT / 'assertions.json').write_text(json.dumps(RESULT, indent=2))
        QTimer.singleShot(250, iface.mainWindow().close)

QTimer.singleShot(2500, run)
