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



    pass  # QGIS not available, skip this test

except ImportError:

                        from qgis.PyQt.QtWidgets import QLineEdit

                            return

                            modal.setProperty('fixture_ready', True)

                            modal.setDirectory(str(ROOT))

                        if not modal.property('fixture_ready'):

                    else:

                        modal.reject()

                    if mode[0] == 'cancel':

                        interactions.append(mode[0] + '-picker')

                    if not interactions or interactions[-1] != mode[0] + '-picker':

                elif isinstance(modal, QFileDialog):

                    QTimer.singleShot(0, modal.button(QMessageBox.No if mode[0] == 'no' else QMessageBox.Yes).click)

                    # nested picker while this timer cannot re-enter its own slot.

                    # Return from timeout first: clicking Yes synchronously opens a

                    interactions.append(mode[0] + '-warning')

                    assert 'sensitive data' in modal.text() and 'confidential' in modal.text()

                if isinstance(modal, QMessageBox) and modal.windowTitle() == 'Save Network Log':

                (ROOT / 'interaction-progress.json').write_text(json.dumps(dict(mode=mode[0], interactions=interactions[-12:], modal=modal.metaObject().className() if modal else None, python_type=type(modal).__name__)))

                modal = QApplication.activeModalWidget()

            def respond():

            KEEP.append(timer)

            timer.setInterval(40)

            timer = QTimer(w)

            mode = ['no']

            target = ROOT / 'synthetic-network-log.json'

            interactions = []

            QApplication.setAttribute(Qt.AA_DontUseNativeDialogs, True)

            # This attribute applies only in this synthetic process, never owner settings.

            # Actual native Save Log C++ lambda, with real warning + Qt file picker.

    

            RESULT['native_curl_action_present_not_triggered'] = True

            assert 'Copy As cURL' in menus and 'Copy as JSON' in menus

            tree.customContextMenuRequested.emit(tree.visualRect(index).center())

            QTimer.singleShot(100, dismiss_menu)

                        menu.close()

                        menus.extend(a.text() for a in menu.actions())

                    if menu.isVisible():

                for menu in tree.findChildren(QMenu):

            def dismiss_menu():

            from qgis.PyQt.QtWidgets import QMenu

            menus = []

            tree.scrollTo(index)

            index = model.index(0, 0)

            QApplication.processEvents()

            tree.show()

            tree.resize(900, 500)

            tree.expandAll()

            panel.show()

            # The rows may be in a hidden developer panel; expose only this scratch app.

            # Activate native context-menu construction but never a clipboard action.

    

            RESULT['disable_preserves_old_rows_but_stops_new_rows'] = True

            assert DEVICE in '\n'.join(values()) and HEADER in '\n'.join(values())

            assert len(posted) == 4 and model.rowCount() == 2

            poll_once()

            assert not record.isChecked()

            record.trigger()

            RESULT['independent_native_header_retained'] = True

            assert HEADER in '\n'.join(values())

            spin(lambda: model.rowCount() == 2)

            native.deleteLater()

            assert native.error() == native.NoError

            spin(native.isFinished)

            native = manager.post(req, b'synthetic=header-fixture')

            req.setRawHeader(b'Authorization', ('Bearer ' + HEADER).encode())

            req = QNetworkRequest(QUrl('http://127.0.0.1:' + str(server.server_port) + '/header-fixture'))

            from qgis.PyQt.QtCore import QUrl

            # Independent native header fixture, NOT a header sent by product transport.

            RESULT['packaged_poll_body_retained'] = True

            assert DEVICE in '\n'.join(values()), 'native recorder did not retain device-code POST body'

    

                return result

                    result += values(index)

                    result.append(str(model.data(index, Qt.DisplayRole)))

                    index = model.index(row, 0, parent)

                for row in range(model.rowCount(parent)):

                result = []

                parent = parent if parent is not None else QModelIndex()

                from qgis.PyQt.QtCore import QModelIndex

            def values(parent=None):

    

            spin(lambda: model.rowCount() == 1)

            assert flow.receive(*reply) and flow.state == 'waiting'

            reply = poll_once()

            assert record.isChecked()

            record.trigger()

            RESULT['recording_off_does_not_add_rows'] = True

            assert len(posted) == 1 and model.rowCount() == 0

            poll_once()

    

                return callbacks[0]

                assert len(callbacks) == 1 and callbacks[0][1:] == (200, {'error': 'authorization_pending'})

                spin(lambda: bool(callbacks))

                assert transport.send(request, lambda *args: callbacks.append(args))

                callbacks = []

            def poll_once():

    

            assert request is not None and request.endpoint == 'token'

            request = flow.poll()

            clock[0] += 1

                               verification_uri='https://github.com/login/device', interval=1, expires_in=60))

            assert flow.receive(initial.key, 200, dict(device_code=DEVICE, user_code='ABCD-EFGH',

            initial = flow.start('SYNTHETIC-RECORDER-CLIENT')

            flow = producer.SessionDeviceFlow(lambda: clock[0])

            clock = [100.0]

            # Construct the token poll through the actual packaged producer; no provider.

            transport = LoopbackTransport(w)

    

                    return 'http://127.0.0.1:' + str(server.server_port) + '/' + endpoint

                def _endpoint_url(self, endpoint):

            class LoopbackTransport(transport_module.GitHubDeviceTransport):

    

            producer = module('github_session')

            transport_module = module('github_transport')

            manager = QgsNetworkAccessManager.instance()

            threading.Thread(target=server.serve_forever, daemon=True).start()

            server.daemon_threads = True

            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)

    

                    self.wfile.write(data)

                    self.end_headers()

                    self.send_header('Content-Length', str(len(data)))

                    self.send_header('Content-Type', 'application/json')

                    self.send_response(200)

                    data = json.dumps({'error': 'authorization_pending'}).encode()

                    posted.append((self.path, body, self.headers.get('Authorization', '')))

                    body = self.rfile.read(int(self.headers['Content-Length']))

                def do_POST(self):

                    pass

                def log_message(self, *args):

            class Handler(BaseHTTPRequestHandler):

    

            posted = []

            assert model.rowCount() == 0

            assert record and save and clear and not record.isChecked()

            clear = panel.findChild(QAction, 'mActionClear')

            save = panel.findChild(QAction, 'mActionSaveLog')

            record = panel.findChild(QAction, 'mActionRecord')

            assert model.sourceModel().metaObject().className() == 'QgsNetworkLogger'

            model = tree.model()

                        if o.metaObject().className() == 'QgsNetworkLoggerTreeView')

            tree = next(o for o in panel.findChildren(QTreeView)

            panel = panels[0]

            assert len(panels) == 1

                      if o.metaObject().className() == 'QgsNetworkLoggerPanelWidget']

            panels = [o for o in w.findChildren(QObject)

            w = iface.mainWindow()

            assert len(DEVICE) == 40

                          settings=str(settings), auth_path=str(auth), platform=QApplication.platformName())

            RESULT.update(pid=os.getpid(), qgis_version=Qgis.QGIS_VERSION, profile=str(profile),

            assert not iface.mainWindow().isWindowModified()

            assert all(p.is_relative_to(ROOT) for p in (profile, settings, auth)), 'native profile isolation'

            auth = Path(QgsApplication.qgisAuthDatabaseFilePath()).resolve()

            settings = Path(QgsSettings().fileName()).resolve()

            profile = Path(QgsApplication.qgisSettingsDirPath()).resolve()

            assert (ROOT / 'SYNTHETIC-ONLY').read_text() == 'recorder-v1'

            assert ROOT.name.startswith('aggis-recorder-')

            assert ROOT.is_relative_to(Path('C:/Users/Michael/AppData/Local/hermes/cache/scratch').resolve())

        try:

        transport = None

        server = None

    def run():

    

    

        return mod

        assert Path(mod.__file__).resolve() == PLUGIN / (name + '.py')

        spec.loader.exec_module(mod)

        sys.modules[spec.name] = mod

        mod = importlib.util.module_from_spec(spec)

        assert spec is not None and spec.loader is not None

        spec = importlib.util.spec_from_file_location('recorder_' + name, PLUGIN / (name + '.py'))

    def module(name):

    

    

        assert predicate(), 'native recorder event deadline'

            time.sleep(.005)

            QApplication.processEvents(QEventLoop.AllEvents, 20)

        while not predicate() and time.monotonic() < until:

        until = time.monotonic() + seconds

    def spin(predicate, seconds=6):

    

    

    HEADER = 'SYNTHETIC-RECORDER-HEADER'

    DEVICE = 'SYNTHETIC-RECORDER-' + 'd' * 21

    KEEP = []

              'curl_action_executed': False, 'branded_acceptance': False}

    RESULT = {'passed': False, 'real_credentials_cleared': False, 'clipboard_touched': False,

    PLUGIN = Path(os.environ['AGGIS_RECORDER_PLUGIN']).resolve()

    ROOT = Path(os.environ['AGGIS_RECORDER_SCRATCH']).resolve()

    

    from qgis.utils import iface

    from qgis.PyQt.QtWidgets import QApplication, QAction, QTreeView, QMessageBox, QFileDialog

    from qgis.PyQt.QtNetwork import QNetworkRequest

    from qgis.PyQt.QtCore import QTimer, QEventLoop, Qt, QObject

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication, QgsNetworkAccessManager, QgsSettings, Qgis
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

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


