"""Offline real-QGIS/Qt update tests; never writes a normal profile."""

import os

from pathlib import Path

import sys

import tempfile

import zipfile

import hashlib

import subprocess

import unittest

from unittest.mock import Mock, patch



os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))

    pass  # QGIS not available, skip this test

except ImportError:

            from qgis.PyQt import sip

            from qgis.gui import QgsMessageBar

        def test_unload_after_native_message_bar_dismissal(self):

    

            self.assertTrue(c.dialog.check.isEnabled())

            c.open()

            self.assertIsNone(c.reply)

            self.assertTrue(replies[-1].aborted)

            c.dialog.reject()

            self.assertFalse(c.dialog.check.isEnabled())

            self.assertTrue(c.dialog.cancel.isEnabled())

            c.open()

            c.check_now(background=True)

            c = self.make_controller()

            self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]

            replies = []

        def test_open_mid_request_exposes_cancel_and_dismiss_cancels(self):

    

            self.assertFalse(staged.exists())

            self.assertIsNone(c._download_file)

            c.cancel()

            c._download_file = failing

            failing.close.side_effect = failed_close

                raise OSError("Synthetic disk close failure")

                output.close()

            def failed_close():

            failing = Mock(wraps=output)

            output = c._download_file

            staged = c._download_path

            c.download()

            self.assertIn("too large", c.status_text)

            self.assertTrue(replies[-1].aborted)

            replies[-1].metaDataChanged.emit()

            replies[-1].setHeader(QNetworkRequest.ContentLengthHeader, 101)

            c.download()

            c.release = dict(version="99.0.0", channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256="a" * 64, size=100, notes="Test", restart_required=True, data_upgrade=False)

            c = self.make_controller()

            self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]

            replies = []

        def test_download_headers_and_disk_close_failure_are_safe(self):

    

            self.assertFalse(list(c.cache_root.rglob("*.zip")))

            c.close()

            self.assertTrue(list(c.cache_root.rglob("*.zip")))

            c.install_package(self.package())  # Refused source install, no modal.

            c = self.make_controller()

        def test_staging_is_cleaned_on_close_unless_native_handoff(self):

    

            c.close()

                install.assert_not_called()

                c.choose_zip()

            with patch.object(updates.QFileDialog, "getOpenFileName", return_value=("", "ZIP")), patch.object(c, "install_package") as install:

            self.assertIn("invalid catalogue", c.status_text)

            replies[-1].deliver(b"invalid JSON")

            c.check_now()

                self.assertFalse(c.dialog.download.isEnabled())

                self.assertIn(expected, c.status_text)

                replies[-1].deliver(json.dumps(dict(schema_version=1, releases=[item])).encode())

                c.check_now()

            for item, expected in ((release, "current"), (dict(release, version="99.0.0", qgis_minimum="9.0"), "different QGIS")):

            release = dict(version=c.installed["version"], channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256="a" * 64, size=123, notes="Test", restart_required=True, data_upgrade=False)

            c.open()

            c = self.make_controller()

            self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]

            replies = []

        def test_current_incompatible_bad_catalogue_and_offline_cancel(self):

    

    

            self.network.get.assert_not_called()

            self.iface.messageBar().pushMessage.assert_called_once()

            self.assertEqual(json.loads(pending_path.read_text())["status"], "acknowledged")

            self.assertIn(str(backup), c.status_text)

            self.assertIn("99.0.0", c.status_text)

            c.open()

            c.start()

            c = self.make_controller(plugin_dir=plugin)

            metadata.write_text(metadata.read_text().replace("1.0.0", "99.0.0"))

            metadata = plugin / "metadata.txt"

            c.close()

            self.assertIn("not confirmed", c.status_text)

            c.start()

            c = self.make_controller(plugin_dir=plugin)

            self.assertTrue(c.closed)

            self.assertEqual(updates.read_installed(backup)["version"], "1.0.0")

            self.assertTrue((backup / "metadata.txt").is_file())

            backup = Path(pending["backup"])

            self.assertEqual(pending["expected_version"], "99.0.0")

            pending = json.loads(pending_path.read_text())

            pending_path = self.root / "recovery" / "pending.json"

                self.assertTrue(handed_path.is_file(), "ZIP must survive native unload before extraction")

                handed_path = Path(installer.installFromZipFile.call_args.args[0])

                installer.installFromZipFile.assert_called_once()

                c.install_package(package)

                installer.installFromZipFile.side_effect = lambda path: c.close() or True

                confirm.return_value = updates.QMessageBox.Yes

                self.assertIn("not authenticated", confirm.call_args.args[2])

                self.assertFalse((self.root / "recovery").exists())

                installer.installFromZipFile.assert_not_called()

                c.install_package(package)

            with patch.object(native_module, "HOME_PLUGIN_PATH", str(profile_plugins)), patch.object(pyplugin_installer, "instance", return_value=installer), patch.object(updates.QMessageBox, "question", return_value=updates.QMessageBox.No) as confirm:

            installer = Mock()

            QgsProject.instance().setDirty(False)

            c.open()

            c = self.make_controller(plugin_dir=plugin)

            package = self.package()

            plugin = profile_plugins / "ag_tech_tooling"

                archive.extractall(profile_plugins)

            with zipfile.ZipFile(self.package(version="1.0.0")) as archive:

            profile_plugins = self.root / "profile" / "python" / "plugins"

            import pyplugin_installer.installer as native_module

            import pyplugin_installer

        def test_confirmed_native_handoff_snapshot_and_next_start_acknowledgement(self):

    

    

            self.assertFalse((self.root / "recovery").exists())

                native.assert_not_called()

                    QgsProject.instance().setDirty(False)

                    QgsProject.instance().removeMapLayer(layer.id())

                    layer.rollBack()

                    self.assertIn("editing", c.status_text)

                    c.install_package(self.package())

                    QgsProject.instance().setDirty(False)

                    layer.startEditing()

                    QgsProject.instance().addMapLayer(layer)

                    layer = QgsVectorLayer("Point?crs=EPSG:4326", "synthetic", "memory")

                    QgsProject.instance().setDirty(False)

                    self.iface.actionSaveProject().trigger.assert_called_once()

                    c.dialog.save.click()

                    self.iface.actionSaveProject.assert_not_called()

                    self.assertIn("Save", c.status_text)

                    c.install_package(self.package())

                    QgsProject.instance().setDirty(True)

                    self.assertIn("Preview", c.status_text)

                    c.install_package(self.package(experimental=True))

                with patch.object(c, "_profile_plugin_dir", return_value=c.plugin_dir):

                self.assertIn("profile", c.status_text)

                c.install_package(self.package())

                self.assertIn("rejected", c.status_text)

                c.install_package(bad)

            with patch.object(pyplugin_installer, "instance") as native:

            bad.write_bytes(b"not a ZIP")

            bad = self.root / "bad.zip"

            c.open()

            c = self.make_controller()

            from qgis.core import QgsVectorLayer

            import pyplugin_installer

        def test_install_rejects_unsafe_source_preview_dirty_and_editable(self):

    

            return path

                archive.writestr("ag_tech_tooling/plugin.py", "# synthetic fixture\n")

                archive.writestr("ag_tech_tooling/__init__.py", "# synthetic fixture\n")

                archive.writestr("ag_tech_tooling/metadata.txt", "[general]\nversion=" + version + "\nqgisMinimumVersion=3.28\nexperimental=" + str(experimental).lower() + "\n")

            with zipfile.ZipFile(path, "w") as archive:

            path = self.root / "fixture.zip"

        def package(self, version="99.0.0", experimental=False):

    

            self.assertFalse(c.dialog.download.isEnabled())

            self.assertEqual(c.dialog.notes.toPlainText(), "")

            c.check_now()

            c.dialog.notes.setPlainText("Changes from a previous check")

            c.open()

            c = self.make_controller()

            self.network.get.side_effect = FakeReply

        def test_recheck_clears_stale_release_notes(self):

    

    

            self.assertFalse(c.daily_timer.isActive())

            self.assertIsNone(c.dialog)

            c.close()

            c.close()

            self.network.get.assert_not_called()

            app.processEvents()

            self.assertIs(c.dialog, dialog)

            c.open()

            dialog.reject()

            self.assertIn("IP", dialog.privacy.text())

            self.assertIn("Installed", dialog.installed.text())

            self.assertEqual(dialog.channel.currentData(), "stable")

            self.assertFalse(dialog.background.isChecked())

            self.assertEqual(dialog.parent(), self.window)

            self.assertFalse(dialog.isModal())

            self.assertTrue(dialog.isVisible())

            dialog = c.dialog

            c.open()

            c.start()

            c.start()

            c = self.make_controller()

        def test_default_offline_reuses_nonmodal_dialog(self):

    

            self.assertFalse(c.daily_timer.isActive())

            c.dialog.background.setChecked(False)

            c.open()

            self.assertEqual(len(replies), 3, "No repeated checks within a day")

            c.daily_timer.timeout.emit()

            self.iface.messageBar().pushWidget.assert_called_once()

            self.assertFalse(c.dialog.isVisible(), "Background check must not pop a dialog")

            replies[-1].deliver(payload)

            self.assertEqual(len(replies), 3)

                spin(10)

                c.start()

            with patch.object(updates, "STARTUP_DELAY_MS", 1):

            c.dialog.reject()

            self.assertTrue(c.daily_timer.isActive())

            self.assertTrue(self.settings.value(updates.PREFIX + "enabled", type=bool))

            c.dialog.background.setChecked(True)

            self.assertEqual(c.release["version"], "100.0.0")

            replies[-1].deliver(payload)

            c.check_now()

            self.assertEqual(self.settings.value(updates.PREFIX + "channel"), "preview")

            self.assertIsNone(c.release)

            c.dialog.channel.setCurrentIndex(1)

            self.assertFalse(c.dialog.windowIcon().isNull(), "Use the product identity on update windows")

            self.assertIn(c.qgis_version, c.dialog.runtime.text())

            self.assertIn("QGIS 3.28", c.status_text, "Explain the offered runtime requirement")

            self.assertIn("restart", c.status_text.lower())

            self.assertIn("data", c.status_text.lower())

            self.assertEqual(c.dialog.notes.toPlainText(), "Plain release notes")

            self.assertEqual(c.release["version"], "99.0.0")

            replies[-1].deliver(payload)

            c.check_now()

            payload = json.dumps(dict(schema_version=1, releases=[stable, preview])).encode()

            preview = dict(stable, version="100.0.0", channel="preview", notes="Preview notes")

            stable = dict(version="99.0.0", channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256="a" * 64, size=123, notes="Plain release notes", restart_required=True, data_upgrade=True)

            c.open()

            c = self.make_controller()

            self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]

            replies = []

        def test_channel_release_notes_and_opt_in_daily_notification(self):

    

            self.assertIsNone(c.parent(), "Closed controllers must not remain owned by main window")

            c.close()

            self.assertFalse(c.dialog.offline.isEnabled())

            c.check_now()

            self.assertFalse(c.dialog.download.isEnabled())

            c.dialog.channel.setCurrentIndex(1)

            self.assertTrue(c.dialog.download.isEnabled())

            self.assertEqual(c.dialog.notes.toPlainText(), release["notes"])

            c.open()

            self.assertIsNone(c.notice)

            next(b for b in buttons if b.text() == "Later").click()

            buttons = c.notice.findChildren(updates.QPushButton)

            self.assertIsNotNone(c.notice)

            self.assertIsNone(c.dialog)

            replies[-1].deliver(json.dumps(dict(schema_version=1, releases=[release])).encode())

            release = dict(version="99.0.0", channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256="a" * 64, size=100, notes="Saved background notes", restart_required=True, data_upgrade=False)

            c.check_now(background=True)

            c = self.make_controller()

            self.settings.setValue(updates.PREFIX + "enabled", True)

            self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]

            replies = []

            self.iface.messageBar.return_value = bar

            bar = QgsMessageBar(self.window)

            from qgis.gui import QgsMessageBar

        def test_background_result_opens_with_notes_later_and_disabled_selection(self):

    

            self.assertIn("timed out", c.status_text)

            self.assertTrue(replies[-1].aborted)

                spin(10)

                c.check_now()

            with patch.object(updates, "NETWORK_TIMEOUT_MS", 1):

            self.assertIn("redirect", c.status_text)

            self.assertEqual(len(replies), 3)

            replies[-1].deliver(status=302, redirect="https://evil.invalid/catalog.json")

            c.check_now()

            self.assertIn("TLS", c.status_text)

            self.assertTrue(replies[-1].aborted)

            replies[-1].sslErrors.emit([])

            c.check_now()

            self.assertIn("too large", c.status_text)

            self.assertLessEqual(len(c._buffer), updates.MAX_CATALOG_BYTES)

            self.assertTrue(reply.aborted, "Oversize catalogue must abort before finish")

            reply.readyRead.emit()

            reply.data = b"x" * (updates.MAX_CATALOG_BYTES + 1)

            reply = replies[-1]

            c.check_now()

            c.open()

            c = self.make_controller()

            self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]

            replies = []

        def test_network_bounds_tls_redirect_timeout(self):

    

            self.assertIsNone(c.dialog)

            self.assertIsNone(c.reply)

            current.finished.emit()

            self.assertTrue(current.aborted)

            c.close()

            current = replies[-1]

            c.dialog.check.click()

            self.assertIn("Cancelled", c.dialog.status.text())

            self.assertIsNone(c.reply)

            self.assertTrue(current.aborted)

            c.dialog.cancel.click()

            current = replies[-1]

            c.dialog.check.click()

            self.assertIn("unavailable", c.dialog.status.text().lower())

            replies[-1].deliver(error="Synthetic offline")

            c.dialog.check.click()

            self.assertNotIn("up to date", c.dialog.status.text().lower())

            self.assertIn("unavailable", c.dialog.status.text().lower())

            spin()

            QTimer.singleShot(0, lambda: replies[-1].deliver(b'{"schema_version":1,"releases":[]}'))

            self.assertEqual(replies[-1].request().attribute(QNetworkRequest.RedirectPolicyAttribute), QNetworkRequest.ManualRedirectPolicy)

            self.assertEqual(len(replies), 1)

            c.dialog.check.click()

            c.open()

            c = self.make_controller()

            self.network.get.side_effect = get

                return reply

                replies.append(reply)

                reply = FakeReply(request)

            def get(request):

            replies = []

        def test_manual_check_empty_error_retry_cancel_and_unload(self):

    

            return self.controller

                                                    cache_root=self.root / "cache", recovery_root=self.root / "recovery", **kwargs)

            self.controller = updates.UpdateActions(self.iface, settings=self.settings, network=self.network,

        def make_controller(self, **kwargs):

    

            self.temp.cleanup()

            app.processEvents()

            self.window.close()

                self.controller.close()

            if self.controller:

        def tearDown(self):

    

            self.controller = None

            self.network = Mock()

            self.iface.mainWindow.return_value = self.window

            self.iface = Mock()

            self.window = QMainWindow()

            self.settings = QSettings(str(self.root / "settings.ini"), QSettings.IniFormat)

            self.root = Path(self.temp.name)

            self.temp = tempfile.TemporaryDirectory(prefix="aggis-update-test-", dir=suite_home.name)

        def setUp(self):

    class UpdateTests(unittest.TestCase):

    

    

    app.initQgis()

    app = QgsApplication([], False, str(Path(suite_home.name) / "qgis-profile"))

    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(Path(suite_home.name) / "settings"))

    QSettings.setDefaultFormat(QSettings.IniFormat)

    suite_home = tempfile.TemporaryDirectory(prefix="aggis-updates-suite-", dir=scratch, ignore_cleanup_errors=True)

    scratch.mkdir(parents=True, exist_ok=True)

    scratch = Path(os.environ.get("TMPDIR") or Path.home() / "AppData/Local/hermes/cache/scratch")

    

    from ag_tech_tooling import updates

    from qgis.PyQt.QtWidgets import QMainWindow

        loop.exec()

        QTimer.singleShot(milliseconds, loop.quit)

        loop = QEventLoop()

    def spin(milliseconds=5):

    

    

            self.finished.emit()

            self.readyRead.emit()

            self.data += data

                self.setError(QNetworkReply.HostNotFoundError, error)

            if error:

                self.setAttribute(QNetworkRequest.RedirectionTargetAttribute, QUrl(redirect))

            if redirect:

            self.setAttribute(QNetworkRequest.HttpStatusCodeAttribute, status)

        def deliver(self, data=b"", status=200, error=None, redirect=None):

    

            self.finished.emit()

            self.setError(QNetworkReply.OperationCanceledError, "Cancelled")

            self.aborted = True

        def abort(self):

    

            return result

            result, self.data = self.data[:count], self.data[count:]

        def readData(self, count):

    

            return len(self.data) + super().bytesAvailable()

        def bytesAvailable(self):

    

            self.aborted = False

            self.data = b""

            self.open(QIODevice.ReadOnly | QIODevice.Unbuffered)

            self.setUrl(request.url())

            self.setRequest(request)

            super().__init__()

        def __init__(self, request):

        """Real Qt signals/device, with controlled bytes and no sockets."""

    class FakeReply(QNetworkReply):

    

    

    import json

    from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply

    from qgis.PyQt.QtCore import QSettings, QTimer, QEventLoop, QIODevice, QUrl

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication, QgsProject
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

        self.iface.messageBar.return_value = QgsMessageBar(self.window)

        c = self.make_controller()

        c._notify()

        sip.delete(c.notice)  # Native message bar can delete its own item.

        c.close()

        self.assertIsNone(c.notice)

        self.assertIsNone(c.dialog)



    @unittest.skipUnless(os.name == "nt", "Windows junction safety")

    def test_native_target_junction_is_refused_before_confirmation(self):

        import pyplugin_installer.installer as native_module

        plugins = self.root / "real-plugins"

        with zipfile.ZipFile(self.package(version="1.0.0")) as archive:

            archive.extractall(plugins)

        alias = self.root / "linked-plugins"

        process = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(plugins)], capture_output=True, text=True)

        self.assertEqual(process.returncode, 0, process.stderr)

        try:

            c = self.make_controller(plugin_dir=plugins / "ag_tech_tooling")

            with patch.object(native_module, "HOME_PLUGIN_PATH", str(alias)), patch.object(updates.QMessageBox, "question", return_value=updates.QMessageBox.No) as question:

                c.install_package(self.package())

                question.assert_not_called()

                self.assertIn("profile", c.status_text)

        finally:

            os.rmdir(alias)  # Remove the junction itself, never its contents.



    def test_staging_precedes_confirmation_and_failed_backup_blocks_install(self):

        import pyplugin_installer

        import pyplugin_installer.installer as native_module

        plugins = self.root / "profile" / "python" / "plugins"

        with zipfile.ZipFile(self.package(version="1.0.0")) as archive:

            archive.extractall(plugins)

        c = self.make_controller(plugin_dir=plugins / "ag_tech_tooling")

        original = self.package()

        expected = original.read_bytes()

        captured = []

        def choose(*args):

            # The source changes while the user is reading the confirmation.

            original.write_bytes(b"changed after verification")

            captured.extend(c.cache_root.rglob("*.zip"))

            return updates.QMessageBox.Yes

        with patch.object(native_module, "HOME_PLUGIN_PATH", str(plugins)), patch.object(updates.QMessageBox, "question", side_effect=choose), patch.object(pyplugin_installer, "instance") as native, patch("ag_tech_tooling.update_catalog.snapshot_plugin", side_effect=OSError("synthetic backup failure")):

            QgsProject.instance().setDirty(False)

            c.install_package(original)

            self.assertTrue(captured, "Stage and verify immutable candidate before consent")

            self.assertEqual(captured[0].read_bytes(), expected)

            native.assert_not_called()

            self.assertIn("before installation", c.status_text)

            self.assertFalse(c.pending_path.exists())



    def test_package_download_trusted_redirect_stream_bounds_and_cancel(self):

        replies = []

        self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]

        c = self.make_controller()

        c.open()

        data = self.package().read_bytes()

        release = dict(version="99.0.0", channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256=hashlib.sha256(data).hexdigest(), size=len(data), notes="Notes", restart_required=True, data_upgrade=False)

        c.release = release

        c.download()

        self.assertEqual(replies[-1].url().toString(), release["url"])

        replies[-1].deliver(status=302, redirect="https://release-assets.githubusercontent.com/asset.zip?sig=synthetic")

        self.assertEqual(len(replies), 2)

        with patch.object(c, "install_package") as install:

            QTimer.singleShot(0, lambda: replies[-1].deliver(data))

            spin()

            path = Path(install.call_args.args[0])

            self.assertEqual(path.read_bytes(), data)

            self.assertEqual(install.call_args.args[1], release)

        c.release = release

        c.download()

        replies[-1].deliver(status=302, redirect="http://release-assets.githubusercontent.com/asset.zip")

        self.assertEqual(len(replies), 3)

        self.assertIn("redirect", c.status_text)

        c.download()

        current = replies[-1]

        staged = c._download_path

        current.deliver(data + b"extra")

        self.assertTrue(current.aborted)

        self.assertFalse(staged.exists())

        c.download()

        staged = c._download_path

        c.cancel()

        self.assertFalse(staged.exists())

        self.assertIsNone(c._download_file)

        with patch.object(updates.QFileDialog, "getOpenFileName", return_value=(str(self.package()), "ZIP")), patch.object(c, "install_package") as install:

            c.dialog.offline.click()

            self.assertEqual(Path(install.call_args.args[0]), self.root / "fixture.zip")

        self.assertIsNone(c.reply)





if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(UpdateTests))

    app.exitQgis()

    suite_home.cleanup()

    sys.exit(not result.wasSuccessful())


